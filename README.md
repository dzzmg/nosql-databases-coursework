# NoSQL Databases Coursework: MongoDB & Neo4j

Practical work from the *Advanced Databases* course (MSc, Astana IT University): data import and aggregation in MongoDB, a sharded MongoDB cluster, and graph queries in Neo4j.

| Folder | Topic | Highlights |
|---|---|---|
| [`mongodb-weblogs-import/`](mongodb-weblogs-import) | ETL: CSV → JSON → MongoDB, analytical queries | Validating converter with error handling, Extended JSON dates, indexes, 8 aggregation pipelines, `explain()` index check |
| [`mongodb-sharded-cluster/`](mongodb-sharded-cluster) | Horizontal scaling | Config server replica set (3 nodes), 2 shards, `mongos` router, hashed shard key, 100,000 documents distributed ~50/50 |
| [`neo4j-social-network/`](neo4j-social-network) | Graph database | Social network model (12 people, 20 friendships, interest groups), friends-of-friends, aggregation, visual styling by query results |

## 1. Web server logs in MongoDB
**`csv_to_json.py`** converts web server logs (`URL, IP, timeStamp, timeSpent`) to JSON:
- validates every row: URL format, IPv4 address, real date and time, whole non-negative seconds, column count
- skips invalid rows with a message and can save them to a separate CSV (`--errors`)
- writes dates as MongoDB Extended JSON (`{"$date": ...}`) so they are stored as real dates
- clear errors for a missing file, an empty file or a wrong header

```bash
cd mongodb-weblogs-import
python3 csv_to_json.py web_logs.csv web_logs.json --errors rejected_rows.csv
# Rows read: 105, Converted: 92, Skipped (error): 12, Empty lines: 1

mongod --dbpath ./data/db          # in another terminal (mkdir -p data/db first)
mongosh                            # started from this folder
> load("load_logs.js")             # inserts 92 documents, creates indexes on URL, IP, timeStamp
> use weblogs
```
**`task2_queries.js`** (run block by block in `mongosh`):
| Query | Description |
|---|---|
| R1–R4 | Sorted lists: all URLs; IPs for a URL (numeric IP order); URLs in a time range; URLs for an IP |
| A1–A4 | Aggregations: total time per URL; visits per URL; visits per URL per day; visits and time per IP |
| EFFICIENCY | `explain("executionStats")` shows the URL index is used (`totalDocsExamined` = matching documents only) |

Numeric IP sorting uses a small `$reduce` helper that turns `10.0.0.7` into a number, so `192.168.1.5` sorts before `192.168.1.12`.

## 2. Sharded MongoDB cluster
A full sharded cluster on one machine (6 processes): 3 config servers as a replica set (ports 27019–27021), 2 single-node shard replica sets (27018, 27028) and a `mongos` router (27017). The collection `testdb.collection` is sharded on a **hashed** key, then 100,000 documents are inserted and `getShardDistribution()` shows an even split between the shards.

Step-by-step commands: [`mongodb-sharded-cluster/setup-steps.txt`](mongodb-sharded-cluster/setup-steps.txt)

## 3. Neo4j social network
- `social_network.cypher` creates 12 `Person` nodes (name, gender, age, city, interest groups) and 20 `FRIEND` relationships.
- `pw4_all_queries.cypher`: men sorted by age, friends and friends-of-friends of a person, friend counts, group membership and sizes, groups of friends-of-friends, and queries used to color the graph (e.g. people with many/few friends, members of one or both groups).

```cypher
// friends of friends of Aidar (without Aidar and his direct friends), A-Z
MATCH (me:Person {name: "Aidar Nurlanov"})-[:FRIEND]-(:Person)-[:FRIEND]-(fof:Person)
WHERE fof <> me AND NOT (me)-[:FRIEND]-(fof)
RETURN DISTINCT fof.name AS friendOfFriend
ORDER BY friendOfFriend
```

## Tech
MongoDB (mongosh, aggregation framework, indexes, sharding, replica sets) · Neo4j (Cypher) · Python
