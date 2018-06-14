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
        # every element should have coordinates
        node['coord'] = [None, None]
        for attrib in element.attrib:
          if attrib == 'id':
            node['_id'] = element.attrib[attrib]
          if attrib == 'lon':
            node['coord'][0] = float(element.attrib[attrib]) # adds longitude to coordinates
          if attrib == 'lat': 
            node['coord'][1] = float(element.attrib[attrib]) # adds latitude to coordinates
          else:
            node[attrib] = element.attrib[attrib]
        for child in element.iter('tag'):
          # grabs the key and value pairs from each tag. 
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
                  street_type = value.split(' ')[-1] # takes the last word in the street value as the street type
                  street_name = ' '.join(value.split(' ')[0:-1]) # takes everything else as the street name
                  # But some addresses also have a direction (east, west, etc.) after the street type
                  # in these cases, the street type will be the second to last word, and the street name will be 
                  # everything from the start up to that point.
                  if street_type in mapping_directions or street_type in directions:
                    direction = ' ' + street_type
                    street_type = value.split(' ')[-2] # Second to last word in the address
                    street_name = ' '.join(value.split(' ')[0:-2]) # everything from the start up to the second to last word as street name
                  if (street_type in mapping_street_types) or (street_type in expected_street_types):
                    if street_type in mapping_street_types:
                      street_type = mapping_street_types[street_type]
                    value = street_name + ' ' + street_type + direction
                try:
                  # if this is the first address attribute that the function adds to node, it will fail (as node['addr'] still does not exists)
                  node['addr']['street_type'] = street_type
                except KeyError:
                  # Then, first adds the node['addr'] dictionary to node, and then adds the attribute.
                  node['addr'] = {}
                  node['addr']['street_type'] = street_type
              try:
                # The same as before: tries to add the new attribute to the node['addr'] dictionary, which may fail if it still does not exists.
                node['addr'][newTag] = value
              except KeyError:
                # Then, first adds the node['addr'] dictionary to node, and then adds the attribute.
                node['addr'] = {}
                node['addr'][newTag] = value
        for child in element.iter('nd'):
          try:
            # here, we take all the 'nd' childs and add it as a reference to the node element 
            # This will work as a foreign key for the nodes collection.
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

  # create both files - nodes and ways - and populates them with the respective JSON elements
  with codecs.open(file_out_nodes, 'w') as fo_nodes:
    with codecs.open(file_out_ways, 'w') as fo_ways:
      # adds an "[" at the beginning of the files - this way, the json object inside the file will represent and array of objects.
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
      # finally, closes the "]", so the array is complete.
      fo_ways.write('{}]\n')
      fo_nodes.write('{}]\n')

def test():
  process_map('toronto.osm', False)

if __name__ == '__main__':
  test()
