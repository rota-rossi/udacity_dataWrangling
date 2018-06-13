# OpenStreetMap Project #

### Map Area ###

Toronto, ON - Canada

https://www.openstreetmap.org/search?query=toronto#map=11/43.7180/-79.3762

Originally from Rio de Janeiro - Brazil, I moved to Toronto two years ago, and I am still making this city my home. I considered analyzing the map for this city a good challenge, and also a great exercise to know it better.

### Challenges ###

As with any cities in Canada, the first challenge is the bilingual characteristics of the street names. Also, Toronto brings some extra challenges in this aspect: the various types of streets, named in English and French brings some complexity to the process.

- As a starting point, I used the [list of Street Types from Canada Post](https://www.canadapost.ca/tools/pg/manual/PGaddress-e.asp#1441964). I added several others types, as I found them on the map. The final list can be seen in this file: [street_types.json](./street_types.json);

- As expected, the street types weren't consistent. 'Street' for instance, could be found in several formats ("St", "St.", "ST", "STREET", "st", "st.");

- Several addresses have extra information: after the street type, some streets contain the geographic direction. For instance, Queen Street is comprised of Queen Street East and West. This direction information needed to be wrangled, as it was present in several formats ('West,' 'west,' 'W,' 'W.,' 'w,' to name a few.) - It also had to be considered to extract the street type.

- Some streets name could not be parsed this way - "Highway 7", for instance. For those, I created an [exception list](./exception_addresses.json).


The final code for the address wrangling can be seen in this file: [prep_db.py](./prep_db.py).

### Transforming ###

There are two primary entities in the XML file: `nodes` and `ways.` `Nodes` are the points of interest in the map, like amenities, or just a geographical coordinate (for mapping). `Ways` are the streets, and they are comprised of a group of nodes. 

I decided to use the `id` field from the entities, instead of letting MongoDB create it automatically. This way, I could have visibility of the identifiers before loading the data into the database.

I chose to create two separate `JSON` files, and add all nodes that are part of a `way` as an array of `ids` inside the way. MongoDB does not enforce Foreign Key (FK) constraints, but it can use it for aggregations using the `$lookup` function.

### Files/Documents statistics ###

File sizes: 

```
734M toronto.osm
612M toronto.osm_nodes.json
161M toronto.osm_ways.json
```

Database countings:

```
> db.nodes.count();
3024143
> db.ways.count();
497234
>
```


## Some Statistics ###

### Types of Street ###

```
> db.nodes.aggregate([
...     {
...         $match: {"addr.street_type": {$exists: true}}
...     },
...     {
...         $group: {
...             _id: "$addr.street_type",
...             count: {$sum: 1},
...         }
...     },
...     {
...         $sort: {count: -1}
...     },
...     {
...         $limit: 10
...     }
... ])
```
```
{ "_id" : "Avenue", "count" : 58996 }
{ "_id" : "Drive", "count" : 54459 }
{ "_id" : "Road", "count" : 52037 }
{ "_id" : "Street", "count" : 39126 }
{ "_id" : "Crescent", "count" : 24376 }
{ "_id" : "Court", "count" : 15601 }
{ "_id" : "Boulevard", "count" : 14338 }
{ "_id" : "Lane", "count" : 4443 }
{ "_id" : "Place", "count" : 4243 }
{ "_id" : "Trail", "count" : 3898 }
```

### Amenities ###

```
> db.nodes.aggregate([
...     {
...         $match: {"amenity": {$exists: true}}
...     },
...     {
...         $group: {
...             _id: "$amenity",
...             count: {$sum: 1},
...         }
...     },
...     {
...         $sort: {count: -1}
...     },
...     {
...         $limit: 10
...     }
... ])
```

```
{ "_id" : "restaurant", "count" : 2729 }
{ "_id" : "fast_food", "count" : 2564 }
{ "_id" : "bench", "count" : 2033 }
{ "_id" : "cafe", "count" : 1308 }
{ "_id" : "post_box", "count" : 1285 }
{ "_id" : "parking", "count" : 1073 }
{ "_id" : "waste_basket", "count" : 1002 }
{ "_id" : "bank", "count" : 870 }
{ "_id" : "fuel", "count" : 682 }
{ "_id" : "pharmacy", "count" : 636 }
```

### Pharmacy Chains ###
```
> db.nodes.aggregate([
...     {$match: {amenity: 'pharmacy'}},
...     {$group: {_id: '$name', count: {$sum:1}}},
...     {$sort: {count: -1}},
...     {$limit: 3}
...     ]);
```

```
{ "_id" : "Shoppers Drug Mart", "count" : 179 }
{ "_id" : "Rexall", "count" : 27 }
{ "_id" : "Main Drug Mart", "count" : 24 }
```

### Total and Top Contributors ###


```
> db.nodes.distinct('user').length
2023
```

```
  const total_nodes = db.nodes.count()

  db.nodes.aggregate([
    {$match: {"user": {$exists: true}}},
    {$group: {
       _id: "$user", 
        count: {$sum:1}
      }
    },
    {
      $project: {
        _id: 1,
        count: 1,
        percentage: {
          $multiply: [
            {$divide: ["$count", total_nodes]}, 
            100
          ]
        }
      }
    },
    {$sort: {count: -1}},
    {$limit: 10}
    ]);
```
```
{ "_id" : "andrewpmk", "count" : 1673705, "percentage" : 55.344770402722354 }
{ "_id" : "Kevo", "count" : 291148, "percentage" : 9.627454786364268 }
{ "_id" : "Matthew Darwin", "count" : 221406, "percentage" : 7.32128077276769 }
{ "_id" : "Victor Bielawski", "count" : 119649, "percentage" : 3.9564597309055825 }
{ "_id" : "Bootprint", "count" : 99285, "percentage" : 3.2830788755690454 }
{ "_id" : "MikeyCarter", "count" : 80210, "percentage" : 2.6523216660058737 }
{ "_id" : "Mojgan Jadidi", "count" : 45451, "percentage" : 1.502938187777496 }
{ "_id" : "geobase_stevens", "count" : 32836, "percentage" : 1.0857952153717598 }
{ "_id" : "Gerit Wagner", "count" : 28284, "percentage" : 0.9352732327803281 }
{ "_id" : "andrewpmk_imports", "count" : 22579, "percentage" : 0.7466247462504253 }
```

We can see the most of contributions (~55% of total) are made by a single user, "andrewpmk."

### Considerations ###

I think that one significant pain point is the rather small number of contributors (around 2000). For a large city like Toronto, we could have a lot more. Maybe integrating with some mapping tools (like Waze, Google Maps, Apple Maps), or even 'geographical games' (like Pokemon Go or Geocaching) can increase the number of contributors, without requiring that they actively add/edit elements in the maps.

### Conclusion ###

After looking at this dataset, it is clear that the data needs more treatment for consistency. I tried to focus my wrangling on two aspects of the street address: street type and directions, and even that brings lots of challenges. Possibly this is a consequence of the 'open' aspect from OpenStreetMaps, and with the time and contributions from users, the data may tend to be more consistent.

