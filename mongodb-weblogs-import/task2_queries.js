// ============================================================
// Practical Work #3 - Task 2: queries on the web server logs
// Database: weblogs, collection: logs
// Fields: URL (string), IP (string), timeStamp (Date), timeSpent (number, seconds)
//
// How to use: in mongosh run  use weblogs  first, then copy ONE block
// at a time (between the ==== lines), paste it and press Enter.
// ============================================================


// ==== CHECK: the collection after the import =================
db.logs.countDocuments()

db.logs.find().limit(3)


// ==== HELPER: turn an IP address into a number ===============
// Run this block once before R2 and A4.
// "10.0.0.7" -> 10*256^3 + 0*256^2 + 0*256 + 7, so IPs are sorted
// like numbers (192.168.1.5 before 192.168.1.12), not like text.
var ipToNumber = (field) => ({
  $reduce: {
    input: { $split: [field, "."] },
    initialValue: 0,
    in: { $add: [{ $multiply: ["$$value", 256] }, { $toInt: "$$this" }] }
  }
})


// ==== R1. Sorted list of all resource URLs ===================
db.logs.aggregate([
  { $group: { _id: "$URL" } },          // one result per different URL
  { $sort: { _id: 1 } },                // A -> Z
  { $project: { _id: 0, URL: "$_id" } }
])


// ==== R2. Sorted list of IPs that accessed a given URL =======
db.logs.aggregate([
  { $match: { URL: "/courses/databases" } },   // the given URL (uses the URL index)
  { $group: { _id: "$IP" } },                  // each IP only once
  { $addFields: { ipNumber: ipToNumber("$_id") } },
  { $sort: { ipNumber: 1 } },                  // numeric IP order
  { $project: { _id: 0, IP: "$_id" } }
])


// ==== R3. Sorted list of URLs accessed within a time range ===
db.logs.aggregate([
  { $match: { timeStamp: { $gte: ISODate("2026-10-03T00:00:00Z"),     // from 3 Oct 00:00
                           $lt:  ISODate("2026-10-04T00:00:00Z") } } }, // to 3 Oct 23:59:59
  { $group: { _id: "$URL" } },
  { $sort: { _id: 1 } },
  { $project: { _id: 0, URL: "$_id" } }
])


// ==== R4. Sorted list of URLs accessed by a given IP =========
db.logs.aggregate([
  { $match: { IP: "10.0.0.7" } },       // the given IP (uses the IP index)
  { $group: { _id: "$URL" } },
  { $sort: { _id: 1 } },
  { $project: { _id: 0, URL: "$_id" } }
])


// ==== A1. URLs with total duration of visits, descending =====
db.logs.aggregate([
  { $group: { _id: "$URL", totalTimeSpent: { $sum: "$timeSpent" } } },
  { $sort: { totalTimeSpent: -1, _id: 1 } },
  { $project: { _id: 0, URL: "$_id", totalTimeSpent: 1 } }
])


// ==== A2. URLs with total number of visits, descending =======
db.logs.aggregate([
  { $group: { _id: "$URL", visits: { $sum: 1 } } },
  { $sort: { visits: -1, _id: 1 } },
  { $project: { _id: 0, URL: "$_id", visits: 1 } }
])


// ==== A3. Visits per URL per day in a period =================
// ordered by URL, then by number of visits (descending)
db.logs.aggregate([
  { $match: { timeStamp: { $gte: ISODate("2026-10-01T00:00:00Z"),
                           $lt:  ISODate("2026-10-04T00:00:00Z") } } },   // 1-3 October
  { $group: {
      _id: { URL: "$URL",
             day: { $dateToString: { format: "%Y-%m-%d", date: "$timeStamp" } } },
      visits: { $sum: 1 } } },
  { $sort: { "_id.URL": 1, visits: -1, "_id.day": 1 } },
  { $project: { _id: 0, URL: "$_id.URL", day: "$_id.day", visits: 1 } }
])


// ==== A4. IPs with total visits and total duration ===========
// ordered by IP, then visits (descending), then duration (descending)
db.logs.aggregate([
  { $group: { _id: "$IP",
              visits: { $sum: 1 },
              totalTimeSpent: { $sum: "$timeSpent" } } },
  { $addFields: { ipNumber: ipToNumber("$_id") } },
  { $sort: { ipNumber: 1, visits: -1, totalTimeSpent: -1 } },
  { $project: { _id: 0, IP: "$_id", visits: 1, totalTimeSpent: 1 } }
])


// ==== EFFICIENCY: check that a query uses an index ===========
db.logs.find({ URL: "/courses/databases" }).explain("executionStats").executionStats
