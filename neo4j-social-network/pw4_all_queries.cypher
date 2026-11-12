// =====================================================================
// PRACTICAL WORK #4 - ALL QUERIES (copy ONE block at a time, then Run)
// Database: social network (12 persons, 20 FRIEND relationships)
// The loading script itself is in social_network.cypher
// =====================================================================


// ==== 0. TEST THE CONNECTION =========================================
RETURN "Hello Neo4j" AS message


// ==== 0b. (only if you need to start again) DELETE EVERYTHING ========
MATCH (n) DETACH DELETE n


// ==== 1.5 CHECK THE LOADED DATA ======================================
MATCH (p:Person) WITH count(p) AS people
MATCH ()-[f:FRIEND]->() RETURN people, count(f) AS friendships

// show the whole graph
MATCH (p:Person) OPTIONAL MATCH (p)-[f:FRIEND]->(q) RETURN p, f, q


// ==== 2.1.1 Men, sorted by age (oldest first) ========================
MATCH (p:Person {gender: "male"})
RETURN p.name AS name, p.age AS age
ORDER BY age DESC


// ==== 2.1.2 Friends of Aidar, A-Z ====================================
MATCH (:Person {name: "Aidar Nurlanov"})-[:FRIEND]-(f:Person)
RETURN f.name AS friend
ORDER BY friend


// ==== 2.1.3 Friends of friends of Aidar, A-Z =========================
MATCH (me:Person {name: "Aidar Nurlanov"})-[:FRIEND]-(:Person)-[:FRIEND]-(fof:Person)
WHERE fof <> me AND NOT (me)-[:FRIEND]-(fof)
RETURN DISTINCT fof.name AS friendOfFriend
ORDER BY friendOfFriend


// ==== 2.1.4 Everyone with number of friends, A-Z =====================
MATCH (p:Person)
OPTIONAL MATCH (p)-[:FRIEND]-(f:Person)
RETURN p.name AS name, count(f) AS friends
ORDER BY name


// ==== 2.2.1 List of groups ===========================================
MATCH (p:Person)
UNWIND p.groups AS groupName
RETURN DISTINCT groupName
ORDER BY groupName


// ==== 2.2.2 Groups of one person =====================================
MATCH (p:Person {name: "Daniyar Mukanov"})
UNWIND p.groups AS groupName
RETURN groupName
ORDER BY groupName


// ==== 2.2.3 Groups with number of members (biggest first) ============
MATCH (p:Person)
UNWIND p.groups AS groupName
RETURN groupName, count(p) AS members
ORDER BY members DESC, groupName


// ==== 2.2.4 Persons with number of groups (most first) ===============
MATCH (p:Person)
RETURN p.name AS name, size(p.groups) AS groupCount
ORDER BY groupCount DESC, name


// ==== 2.2.5 Number of groups of Aidar's friends of friends ===========
MATCH (me:Person {name: "Aidar Nurlanov"})-[:FRIEND]-(:Person)-[:FRIEND]-(fof:Person)
WHERE fof <> me AND NOT (me)-[:FRIEND]-(fof)
UNWIND fof.groups AS groupName
RETURN count(DISTINCT groupName) AS totalGroups, collect(DISTINCT groupName) AS groups


// ==== 3.2 friend (red) ===============================================
MATCH (:Person {name: "Aidar Nurlanov"})-[:FRIEND]-(f:Person)
SET f.friend = true
RETURN f.name AS name, f.friend AS friend


// ==== 3.3 twoHandFriend (yellow) =====================================
MATCH (me:Person {name: "Aidar Nurlanov"})-[:FRIEND]-(:Person)-[:FRIEND]-(fof:Person)
WHERE fof <> me AND NOT (me)-[:FRIEND]-(fof)
WITH DISTINCT fof
SET fof.twoHandFriend = true
RETURN fof.name AS name, fof.twoHandFriend AS twoHandFriend


// ==== 3.4a manyFriends (green) =======================================
MATCH (p:Person)
WHERE COUNT { (p)-[:FRIEND]-() } > 5
SET p.manyFriends = true
RETURN p.name AS name, COUNT { (p)-[:FRIEND]-() } AS friends


// ==== 3.4b fewFriends (red) ==========================================
MATCH (p:Person)
WHERE COUNT { (p)-[:FRIEND]-() } < 3
SET p.fewFriends = true
RETURN p.name AS name, COUNT { (p)-[:FRIEND]-() } AS friends


// ==== 3.5a group1 = sports (blue) ====================================
MATCH (p:Person) WHERE "sports" IN p.groups
SET p.group1 = true
RETURN p.name AS name, p.groups AS groups


// ==== 3.5b group2 = games (red) ======================================
MATCH (p:Person) WHERE "games" IN p.groups
SET p.group2 = true
RETURN p.name AS name, p.groups AS groups


// ==== 3.5c bothGroups (purple) =======================================
MATCH (p:Person) WHERE "sports" IN p.groups AND "games" IN p.groups
SET p.bothGroups = true
RETURN p.name AS name, p.groups AS groups


// ==== EXTRA: change a property and a label, then undo ===============
MATCH (p:Person {name: "Kamila Abenova"})
SET p.city = "Almaty", p:Student
RETURN p.name AS name, p.city AS city, labels(p) AS labels

MATCH (p:Person {name: "Kamila Abenova"})
SET p.city = "Astana"
REMOVE p:Student
RETURN p.name AS name, p.city AS city, labels(p) AS labels
