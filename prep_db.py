import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'([a-z]|_)+:([a-z]|_)+')

directions = [
  'East', 'east', 'West', 'west',
  'North', 'north', 'South', 'south'
]

mapping_directions = {
  'E': 'East',
  'e': 'East',
  'east': 'East',
  'E.': 'East',
  'W': 'West',
  'w': 'West',
  'west': 'West',
  'W.': 'West',
  'N': 'North',
  'n': 'North',
  'north': 'North',
  'N.': 'North',
  'S': 'South',
  's': 'South',
  'south': 'South',
  'S.': 'South',
}

with open('expected_street_types.json', 'r') as f:
  expected_street_types = json.load(f)

with open('exception_addresses.json', 'r') as f:
  exception_addresses = json.load(f)

with open('mapping_street_types.json', 'r') as f:
  mapping_street_types = json.load(f)

def shape_element(element):
    node = {}
    if element.tag == 'node' or element.tag == 'way':
        node['type'] = element.tag
        for attrib in element.attrib:
          if attrib == 'id':
            node['_id'] = element.attrib[attrib]
          else:
            node[attrib] = element.attrib[attrib]
        for child in element.iter('tag'):
          attrib = child.attrib['k']
          value = child.attrib['v']
          if lower.search(attrib):
            node[attrib] = value
          elif lower_colon.search(attrib):
            tagType = attrib.split(':')[0]
            newTag = attrib.split(':')[-1]
            if tagType == 'addr':
              if newTag == 'street':
                street_type = 'other'
                if value not in exception_addresses:
                  direction = ''
                  street_type = value.split(' ')[-1]
                  street_name = ' '.join(value.split(' ')[0:-1])
                  if street_type in mapping_directions or street_type in directions:
                    direction = ' ' + street_type
                    street_type = value.split(' ')[-2]
                    street_name = ' '.join(value.split(' ')[0:-2])
                  if (street_type in mapping_street_types) or (street_type in expected_street_types):
                    if street_type in mapping_street_types:
                      street_type = mapping_street_types[street_type]
                    value = street_name + ' ' + street_type + direction
                try:
                  node['addr']['street_type'] = street_type
                except KeyError:
                  node['addr'] = {}
                  node['addr']['street_type'] = street_type
              try:
                node['addr'][newTag] = value
              except KeyError:
                node['addr'] = {}
                node['addr'][newTag] = value
        for child in element.iter('nd'):
          try:
            node['nodes'].append(child.attrib['ref'])
          except KeyError:
            node['nodes'] = []
            node['nodes'].append(child.attrib['ref'])
        return node
    else:
        return None

def process_map(file_in, pretty=False):
  file_out_nodes = '{0}_nodes.json'.format(file_in)
  file_out_ways = '{0}_ways.json'.format(file_in)

  with codecs.open(file_out_nodes, 'w') as fo_nodes:
    with codecs.open(file_out_ways, 'w') as fo_ways:
      fo_nodes.write('[\n')
      fo_ways.write('[\n')
      for _, element in ET.iterparse(file_in):
        el = shape_element(element)
        if el:
          if el['type'] == 'node':
            if pretty:
              fo_nodes.write(json.dumps(el, indent=2)+',\n')
            else:
              fo_nodes.write(json.dumps(el) + ',\n')
          elif el['type'] == 'way':
            if pretty:
              fo_ways.write(json.dumps(el, indent=2)+',\n')
            else:
              fo_ways.write(json.dumps(el) + ',\n')
          element.clear()
      fo_ways.write('{}]\n')
      fo_nodes.write('{}]\n')

def test():
  process_map('toronto.osm', False)

if __name__ == '__main__':
  test()
