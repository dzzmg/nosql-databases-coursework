// load_logs.js - loads the converted JSON logs into MongoDB.
// Practical Work #3, Task 2 (Data Import).
//
// How to run (in the mongosh shell, while the server is running):
//   start mongosh from this folder, then:  load("load_logs.js")

{  // a block, so the script can be loaded again without errors
  const fs = require("fs");
  const file = require("path").join(process.cwd(), "web_logs.json");

  // 1. read the JSON file. EJSON.parse turns {"$date": "..."} into a real Date.
  const docs = EJSON.parse(fs.readFileSync(file, "utf8"));
  print("Documents in the file: " + docs.length);

  // 2. use the database "weblogs" and start with an empty collection "logs"
  db = db.getSiblingDB("weblogs");
  db.logs.drop();

  // 3. insert all documents with one command
  const result = db.logs.insertMany(docs);
  print("Inserted documents:    " + Object.keys(result.insertedIds).length);

  // 4. indexes on the fields that the queries search by
  db.logs.createIndex({ URL: 1 });
  db.logs.createIndex({ IP: 1 });
  db.logs.createIndex({ timeStamp: 1 });
  print("Indexes: " + db.logs.getIndexes().map(i => i.name).join(", "));
}
