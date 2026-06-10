/*
The club is adding a new facility - a spa.
*/

INSERT INTO cd.facilities (
    facid,
    name,
    membercost,
    guestcost,
    initialoutlay,
    monthlymaintenance
)
VALUES (
    9,
    'Spa',
    20,
    30,
    100000,
    800
);


/*
Insert Spa with auto-generated facid.
*/

INSERT INTO cd.facilities (
    facid,
    name,
    membercost,
    guestcost,
    initialoutlay,
    monthlymaintenance
)
VALUES (
    (SELECT MAX(facid) + 1 FROM cd.facilities),
    'Spa',
    20,
    30,
    100000,
    800
);


/*
Fix initial outlay for Tennis Court 2.
*/

UPDATE cd.facilities
SET initialoutlay = 10000
WHERE name = 'Tennis Court 2';


/*
Increase Tennis Court 2 costs by 10% based on Tennis Court 1.
*/

UPDATE cd.facilities
SET
    membercost = 1.1 * (
        SELECT membercost
        FROM cd.facilities
        WHERE name = 'Tennis Court 1'
    ),
    guestcost = 1.1 * (
        SELECT guestcost
        FROM cd.facilities
        WHERE name = 'Tennis Court 1'
    )
WHERE name = 'Tennis Court 2';


/*
Delete all bookings.
*/

DELETE FROM cd.bookings;


/*
Remove member 37.
*/

DELETE FROM cd.members
WHERE memid = 37;


/*
Facilities with low member fee relative to maintenance.
*/

SELECT
    facid,
    name,
    membercost,
    monthlymaintenance
FROM cd.facilities
WHERE membercost > 0
  AND membercost < (1.0 / 50 * monthlymaintenance);


/*
Facilities containing 'Tennis' in name.
*/

SELECT *
FROM cd.facilities
WHERE name LIKE '%Tennis%';


/*
Facilities with ID 1 and 5.
*/

SELECT *
FROM cd.facilities
WHERE facid IN (1, 5);


/*
Members who joined after Sept 2012.
*/

SELECT
    memid,
    surname,
    firstname,
    joindate
FROM cd.members
WHERE joindate >= '2012-09-01';


/*
Union of surnames and facility names.
*/

SELECT surname
FROM cd.members

UNION

SELECT name
FROM cd.facilities;


/*
Bookings for David Farrell.
*/

SELECT
    b.starttime
FROM cd.bookings b
JOIN cd.members m
    ON b.memid = m.memid
WHERE m.firstname = 'David'
  AND m.surname = 'Farrell';


/*
Tennis court bookings on 2012-09-21.
*/

SELECT
    b.starttime,
    f.name
FROM cd.bookings b
JOIN cd.facilities f
    ON b.facid = f.facid
WHERE f.name IN ('Tennis Court 1', 'Tennis Court 2')
  AND b.starttime >= '2012-09-21'
  AND b.starttime < '2012-09-22'
ORDER BY b.starttime;


/*
Members and their recommenders.
*/

SELECT
    m.firstname AS memfname,
    m.surname   AS memsname,
    r.firstname AS recfname,
    r.surname   AS recsname
FROM cd.members m
LEFT JOIN cd.members r
    ON r.memid = m.recommendedby
ORDER BY
    m.surname,
    m.firstname;


/*
Members who recommended others.
*/

SELECT DISTINCT
    r.firstname,
    r.surname
FROM cd.members m
JOIN cd.members r
    ON r.memid = m.recommendedby
ORDER BY
    r.surname,
    r.firstname;


/*
Members with recommender (no JOIN version).
*/

SELECT DISTINCT
    CONCAT(m.firstname, ' ', m.surname) AS member,
    (
        SELECT CONCAT(r.firstname, ' ', r.surname)
        FROM cd.members r
        WHERE r.memid = m.recommendedby
    ) AS recommender
FROM cd.members m
ORDER BY member;


/*
Count of recommendations per member.
*/

SELECT
    recommendedby,
    COUNT(*) AS total_recommendations
FROM cd.members
WHERE recommendedby IS NOT NULL
GROUP BY recommendedby
ORDER BY recommendedby;


/*
Total slots per facility.
*/

SELECT
    f.facid,
    SUM(b.slots) AS total_slots
FROM cd.facilities f
JOIN cd.bookings b
    ON f.facid = b.facid
GROUP BY f.facid
ORDER BY f.facid;


/*
Slots per facility in September 2012.
*/

SELECT
    f.facid,
    SUM(b.slots) AS total_slots
FROM cd.facilities f
JOIN cd.bookings b
    ON f.facid = b.facid
WHERE b.starttime >= '2012-09-01'
  AND b.starttime < '2012-10-01'
GROUP BY f.facid
ORDER BY total_slots;


/*
Slots per facility per month in 2012.
*/

SELECT
    b.facid,
    EXTRACT(MONTH FROM b.starttime) AS month,
    SUM(b.slots) AS total_slots
FROM cd.bookings b
WHERE EXTRACT(YEAR FROM b.starttime) = 2012
GROUP BY
    b.facid,
    month
ORDER BY
    b.facid,
    month;


/*
Distinct members (including guests) with bookings.
*/

SELECT COUNT(DISTINCT memid)
FROM cd.bookings
WHERE slots >= 1;


/*
First booking after Sept 1st 2012 per member.
*/

SELECT
    m.surname,
    m.firstname,
    m.memid,
    MIN(b.starttime) AS first_booking
FROM cd.members m
JOIN cd.bookings b
    ON m.memid = b.memid
WHERE b.starttime > '2012-09-01'
GROUP BY
    m.surname,
    m.firstname,
    m.memid
ORDER BY m.memid;


/*
Member list with total count window function.
*/

SELECT
    COUNT(*) OVER () AS total_count,
    firstname,
    surname
FROM cd.members
ORDER BY joindate;


/*
Monotonic numbering by join date.
*/

SELECT
    ROW_NUMBER() OVER (ORDER BY joindate) AS row_num,
    firstname,
    surname
FROM cd.members;


/*
Facility with highest bookings (ties included).
*/

SELECT facid, total
FROM (
    SELECT
        facid,
        SUM(slots) AS total,
        RANK() OVER (ORDER BY SUM(slots) DESC) AS rnk
    FROM cd.bookings
    GROUP BY facid
) sub
WHERE rnk = 1;


/*
Formatted names.
*/

SELECT CONCAT(surname, ', ', firstname) AS name
FROM cd.members;


/*
Telephone numbers with parentheses pattern.
*/

SELECT
    memid,
    telephone
FROM cd.members
WHERE telephone ~ '^\(\d{3}\) \d{3}-\d{4}$'
ORDER BY memid;


/*
Count members by surname initial.
*/

SELECT
    SUBSTR(surname, 1, 1) AS letter,
    COUNT(*) AS total
FROM cd.members
GROUP BY SUBSTR(surname, 1, 1)
ORDER BY letter;
