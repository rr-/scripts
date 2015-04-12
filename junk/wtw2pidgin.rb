#!/usr/bin/ruby
require 'nokogiri'
doc = Nokogiri.XML(STDIN.read)
STDOUT.set_encoding('cp1250')

group_map = {}

doc.xpath('//Group').each do |group|
  name = group.xpath('Name').text
  id = group.xpath('Id').text
  group_map[id] = name
end

doc.xpath('//Contact').each do |contact|
  name = contact.xpath('ShowName').text
  groups = contact.xpath('Groups//GroupId').map { |node| node.text }
  number = contact.xpath('GGNumber').text
  group_name = group_map[groups[0]]

  dict = {
    name: name,
    group_name: group_name,
    number: number}

  print "%{name};%{name};%{name};%{name};;%{group_name};%{number};\r\n" % dict
end
