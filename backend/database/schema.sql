create table Account (
	id		serial,
	givenName	text			not null,
	familyName	text			not null,
	primary key	(id)
);

create table Adult (
	accountID	serial,
	email		text			not null,
	primary key	(accountID),
	foreign key	(accountID)		references	Account(id)
);

create table Student (
	studentID	serial,
	primary key	(studentID),
	foreign key	(studentID)		references	Account(id)
);

create table Administrator (
	adminID		serial,
	primary key	(adminID),
	foreign key	(adminID)		references	Account(id)
);

create table Teaches (
	adminID		serial,
	studentID	serial,
	foreign key	(adminID)		references	Administrator(id),
	foreign key	(studentID)		references	Student(id),
	primary key	(adminID, studentID)
);

create table Guardian (
	guardianID	serial,
	primary key	(guardianID),
	foreign key	(guardianID)		references	Account(id)
);

create table HasChild (
	studentID	serial,
	guardianID	serial,
	foreign key	(studentID)		references	Student(id),
	foreign key	(guardianID)		references	Guardian(id)
	primary key	(studentID, guardianID)
);

create table OwnsWebsite (
	-- todo: only an administrator or student can own websites.
	-- 'accountID' should only reference either Student(id) or Administrator(id)
	-- the er model should also be updated to reflect that a student only owns
	-- one website, but an administrator can manage every website owned by some students.
	accountID	serial,
	websiteID	serial,
	foreign key	(accountID)		references	Account(id),
	foreign key	(websiteID)		references	Website(id)
	primary key	(accountID, websiteID)
);

create table Website (
	websiteID	serial,
	title		text,
	primary key	(websiteID)
);

create table Webpage (
	-- todo: depict relationship between website and webpage
	webpageID	serial,
	title		text,
	filename	text,
	contents	text,	-- url to HTML file
				-- possibly add stylesheet and script? idk
	primary key	(webpageID)
);
