import asyncio
import sys
from pathlib import Path
from typing import Optional, List
import configargparse
from booru_toolkit import errors
from booru_toolkit import cli
from booru_toolkit import tagger
from booru_toolkit.plugin import Safety
from booru_toolkit.plugin import PluginBase
from booru_toolkit.plugin import PluginYume
from booru_toolkit.plugin import PluginGelbooru


PLUGINS: List[PluginBase] = [PluginGelbooru(), PluginYume()]
SAFETY_MAP = {
    'safe': Safety.Safe,
    'sketchy': Safety.Questionable,
    'questionable': Safety.Questionable,
    'unsafe': Safety.Explicit,
    'explicit': Safety.Explicit,
    's': Safety.Safe,
    'q': Safety.Questionable,
    'e': Safety.Explicit,
}


def parse_args() -> configargparse.Namespace:
    parser = cli.make_arg_parser('Sends post to various boorus.', PLUGINS)
    parser.add(
        '-s', '--safety', metavar='SAFETY', default='safe', required=False,
        choices=SAFETY_MAP.keys(),
        help='post safety ({safe,questionable,explicit})')
    parser.add('--source', default='', help='post source')
    parser.add(
        '-t', '--tags', nargs='*', metavar='TAG',
        help='list of post tags')
    parser.add(
        '-i', '--interactive', action='store_true',
        help='edit tags interactively')
    parser.add(metavar='POST_PATH', dest='path', help='path to the post')
    return parser.parse_args()


async def confirm_similar_posts(plugin: PluginBase, content: bytes) -> None:
    similar_posts = await plugin.find_similar_posts(content)
    if similar_posts:
        print('Similar posts found:')
        for similarity, post in similar_posts:
            print('%.02f: %s (%dx%d)' % (
                similarity,
                post.site_url,
                post.width,
                post.height))
        input('Hit enter to continue, ^C to abort\n')


async def run(args: configargparse.Namespace) -> int:
    plugin: PluginBase = args.plugin
    user_name: str = args.user
    password: str = args.password

    safety: Safety = SAFETY_MAP[args.safety]
    source: Optional[str] = args.source
    initial_tags: List[str] = args.tags or []
    interactive: bool = args.interactive
    path: Path = Path(args.path)

    try:
        if not path.exists():
            raise errors.NoContentError()
        with path.open('rb') as handle:
            content = handle.read()

        print('Logging in...')
        await plugin.login(user_name, password)

        print('Searching for duplicates...')
        post = await plugin.find_exact_post(content)
        if not post:
            await confirm_similar_posts(plugin, content)

        print('Gathering tags...')
        tag_list = tagger.TagList()
        if post:
            for tag in post.tags:
                tag_list.add(tag, tagger.TagSource.Initial)
        for tag in initial_tags:
            tag_list.add(tag, tagger.TagSource.UserInput)
        if interactive:
            result = await tagger.run(
                plugin,
                tag_list,
                'Uploading to {}: {} (safety: {})'.format(
                    plugin.name,
                    path,
                    {
                        Safety.Safe: 'safe',
                        Safety.Questionable: 'questionable',
                        Safety.Explicit: 'explicit',
                    }[safety]))
            if not result:
                print('Aborted.')
                return 0
        tags = [tag.name for tag in tag_list.get_all()]

        print('Tags:')
        print('\n'.join(tags))

        if post:
            await plugin.update_post_tags(post, tags)
            print('Updated.')
        else:
            post = await plugin.upload_post(
                content, source=source, safety=safety, tags=tags)
            print('Uploaded.')

        if post:
            print('Address: ' + post.content_url)
        return 0

    except (errors.ApiError, errors.DuplicateUploadError) as ex:
        print('Error: %s' % str(ex), file=sys.stderr)

    return 1


def main() -> int:
    args = parse_args()
    loop = asyncio.get_event_loop()
    try:
        task = loop.create_task(run(args))
        result = loop.run_until_complete(task)
    except KeyboardInterrupt:
        result = 1
        print('Aborted.')
        task.cancel()  # throw CancelledError wherever the code is running
        loop.run_forever()  # give the task a chance to tidy up
    finally:
        loop.close()
    sys.exit(result)


if __name__ == '__main__':
    main()
