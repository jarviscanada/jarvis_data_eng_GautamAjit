# Introduction

# SQL Queries

###### Table Setup (DDL)

```sql
CREATE DATABASE exercises;
\c exercises
CREATE SCHEMA cd;

CREATE TABLE bookings (
    bookid integer NOT NULL,
    facid integer NOT NULL,
    memid integer NOT NULL,
    starttime timestamp without time zone NOT NULL,
    slots integer NOT NULL
);

CREATE TABLE facilities (
    facid integer NOT NULL,
    name character varying(100) NOT NULL,
    membercost numeric NOT NULL,
    guestcost numeric NOT NULL,
    initialoutlay numeric NOT NULL,
    monthlymaintenance numeric NOT NULL
);

CREATE TABLE members (
    memid integer NOT NULL,
    surname character varying(200) NOT NULL,
    firstname character varying(200) NOT NULL,
    address character varying(300) NOT NULL,
    zipcode integer NOT NULL,
    telephone character varying(20) NOT NULL,
    recommendedby integer,
    joindate timestamp without time zone NOT NULL
);

ALTER TABLE ONLY bookings
    ADD CONSTRAINT bookings_pk PRIMARY KEY (bookid);

ALTER TABLE ONLY facilities
    ADD CONSTRAINT facilities_pk PRIMARY KEY (facid);

ALTER TABLE ONLY members
    ADD CONSTRAINT members_pk PRIMARY KEY (memid);

ALTER TABLE ONLY bookings
    ADD CONSTRAINT fk_bookings_facid FOREIGN KEY (facid) REFERENCES facilities(facid);

ALTER TABLE ONLY bookings
    ADD CONSTRAINT fk_bookings_memid FOREIGN KEY (memid) REFERENCES members(memid);

ALTER TABLE ONLY members
    ADD CONSTRAINT fk_members_recommendedby FOREIGN KEY (recommendedby) REFERENCES members(memid) ON DELETE SET NULL;
```

###### Question 1: Show all members 

```sql
SELECT *
FROM cd.members
```

###### Question 2: The club is adding a new facility - a spa. We need to add it into the facilities table. Use the following values:
###### facid: 9, Name: 'Spa', membercost: 20, guestcost: 30, initialoutlay: 100000, monthlymaintenance: 800.

```sql
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
```

###### Question 3: Let's try adding the spa to the facilities table again. This time, though, we want to automatically generate the value for the next facid, rather than specifying it as a constant. Use the following values for everything else:
###### Name: 'Spa', membercost: 20, guestcost: 30, initialoutlay: 100000, monthlymaintenance: 800.

```sql
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
```

###### Question 4: We made a mistake when entering the data for the second tennis court. The initial outlay was 10000 rather than 8000: you need to alter the data to fix the error.

```sql
UPDATE cd.facilities
SET initialoutlay = 10000
WHERE name = 'Tennis Court 2';
```

###### Question 5: We want to alter the price of the second tennis court so that it costs 10% more than the first one. Try to do this without using constant values for the prices, so that we can reuse the statement if we want to.

```sql
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
```

###### Question 6: As part of a clearout of our database, we want to delete all bookings from the cd.bookings table. How can we accomplish this?

```sql
DELETE FROM cd.bookings;
```

###### Question 7: We want to remove member 37, who has never made a booking, from our database. How can we achieve that?

```sql
DELETE FROM cd.members
WHERE memid = 37;
```

###### Question 8: How can you produce a list of facilities that charge a fee to members, and that fee is less than 1/50th of the monthly maintenance cost? Return the facid, facility name, member cost, and monthly maintenance of the facilities in question.

```sql
SELECT
    facid,
    name,
    membercost,
    monthlymaintenance
FROM cd.facilities
WHERE membercost > 0
  AND membercost < (1.0 / 50 * monthlymaintenance);
```

###### Question 9: How can you produce a list of all facilities with the word 'Tennis' in their name?

```sql
SELECT *
FROM cd.facilities
WHERE name LIKE '%Tennis%';
```

###### Question 10: How can you retrieve the details of facilities with ID 1 and 5? Try to do it without using the OR operator.

```sql
SELECT *
FROM cd.facilities
WHERE facid IN (1, 5); 
```

###### Question 11: How can you produce a list of members who joined after the start of September 2012? Return the memid, surname, firstname, and joindate of the members in question.

```sql
SELECT
    memid,
    surname,
    firstname,
    joindate
FROM cd.members
WHERE joindate >= '2012-09-01';
```

###### Question 12: You, for some reason, want a combined list of all surnames and all facility names. Yes, this is a contrived example :-). Produce that list!

```sql
SELECT surname
FROM cd.members

UNION

SELECT name
FROM cd.facilities;
```
###### Question 13: How can you produce a list of the start times for bookings by members named 'David Farrell'?

```sql
SELECT
    b.starttime
FROM cd.bookings b
JOIN cd.members m
    ON b.memid = m.memid
WHERE m.firstname = 'David'
  AND m.surname = 'Farrell';
```

###### Question 14: How can you produce a list of the start times for bookings for tennis courts, for the date '2012-09-21'? Return a list of start time and facility name pairings, ordered by the time.

```sql
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
```

###### Question 15: How can you output a list of all members, including the individual who recommended them (if any)? Ensure that results are ordered by (surname, firstname).

```sql
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
```

###### Question 16: How can you output a list of all members who have recommended another member? Ensure that there are no duplicates in the list, and that results are ordered by (surname, firstname).

```sql
SELECT DISTINCT
    r.firstname,
    r.surname
FROM cd.members m
JOIN cd.members r
    ON r.memid = m.recommendedby
ORDER BY
    r.surname,
    r.firstname;
```

###### Question 17: How can you output a list of all members, including the individual who recommended them (if any), without using any joins? Ensure that there are no duplicates in the list, and that each firstname + surname pairing is formatted as a column and ordered.
*/

```sql
SELECT DISTINCT
    CONCAT(m.firstname, ' ', m.surname) AS member,
    (
        SELECT CONCAT(r.firstname, ' ', r.surname)
        FROM cd.members r
        WHERE r.memid = m.recommendedby
    ) AS recommender
FROM cd.members m
ORDER BY member; 
```

###### Question 18: Produce a count of the number of recommendations each member has made. Order by member ID.

```sql
SELECT
    recommendedby,
    COUNT(*) AS total_recommendations
FROM cd.members
WHERE recommendedby IS NOT NULL
GROUP BY recommendedby
ORDER BY recommendedby;
```
###### Question 19: Produce a list of the total number of slots booked per facility. For now, just produce an output table consisting of facility id and slots, sorted by facility id.

```sql
SELECT
    f.facid,
    SUM(b.slots) AS total_slots
FROM cd.facilities f
JOIN cd.bookings b
    ON f.facid = b.facid
GROUP BY f.facid
ORDER BY f.facid;
```

###### Question 20: Produce a list of the total number of slots booked per facility in the month of September 2012. Produce an output table consisting of facility id and slots, sorted by the number of slots.

```sql
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
```

###### Question 21: Produce a list of the total number of slots booked per facility per month in the year of 2012. Produce an output table consisting of facility id and slots, sorted by the id and month.

```sql
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
```

###### Question 22: Find the total number of members (including guests) who have made at least one booking.

```sql
SELECT COUNT(DISTINCT memid)
FROM cd.bookings
WHERE slots >= 1;
```

###### Question 23: Produce a list of each member name, id, and their first booking after September 1st 2012. Order by member ID.

```sql
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
```

###### Question 24: Produce a list of member names, with each row containing the total member count. Order by join date, and include guest members.

```sql
SELECT
    COUNT(*) OVER () AS total_count,
    firstname,
    surname
FROM cd.members
ORDER BY joindate;
```

###### Question 25: Produce a monotonically increasing numbered list of members (including guests), ordered by their date of joining. Remember that member IDs are not guaranteed to be sequential.

```sql
SELECT
    ROW_NUMBER() OVER (ORDER BY joindate) AS row_num,
    firstname,
    surname
FROM cd.members;
```

###### Question 26: Output the facility id that has the highest number of slots booked. Ensure that in the event of a tie, all tieing results get output.


```sql
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
```

###### Question 27: Output the names of all members, formatted as 'Surname, Firstname'

```sql
SELECT CONCAT(surname, ', ', firstname) AS name
FROM cd.members;
```

###### Question 28: You've noticed that the club's member table has telephone numbers with very inconsistent formatting. You'd like to find all the telephone numbers that contain parentheses, returning the member ID and telephone number sorted by member ID.

```sql
SELECT
    memid,
    telephone
FROM cd.members
WHERE telephone ~ '^\(\d{3}\) \d{3}-\d{4}$'
ORDER BY memid;
```

###### Question 29: You'd like to produce a count of how many members you have whose surname starts with each letter of the alphabet. Sort by the letter, and don't worry about printing out a letter if the count is 0.

```sql
SELECT
    SUBSTR(surname, 1, 1) AS letter,
    COUNT(*) AS total
FROM cd.members
GROUP BY SUBSTR(surname, 1, 1)
ORDER BY letter;
```
