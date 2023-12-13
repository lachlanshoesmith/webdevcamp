create table Account (
	id					serial,
	givenName			text			not null,
	familyName			text			not null,
	username			varchar(20)		not null	unique,
	password			text			not null,
	registrationDate	timestamp		default		current_timestamp,
	/* salt is username + registrationDate concatenated */
	primary key	(id)
);

create table FullAccount (
	accountID			serial,
	email				text			not null	unique,
	phoneNumber			text,
	primary key			(accountID),
	foreign key			(accountID)		references	Account(id)
);

create table Student (
	studentID			serial,
	primary key			(studentID),
	foreign key			(studentID)		references	Account(id)
);

create table Administrator (
	adminID			serial,
	primary key		(adminID),
	foreign key		(adminID)			references	Account(id)
);

create table Teaches (
	adminID			serial,
	studentID		serial,
	foreign key		(adminID)			references	Administrator(id),
	foreign key		(studentID)			references	Student(id),
	primary key		(adminID, studentID)
);

create table Guardian (
	guardianID		serial,
	primary key		(guardianID),
	foreign key		(guardianID)		references	Account(id)
);

create table HasChild (
	studentID		serial,
	guardianID		serial,
	foreign key		(studentID)			references	Student(id),
	foreign key		(guardianID)		references	Guardian(id)
	primary key		(studentID, guardianID)
);

create table OwnsWebsite (
	accountID		serial,
	websiteID		serial,
	foreign key		(accountID)			references	Account(id),
	foreign key		(websiteID)			references	Website(id)
	primary key		(accountID, websiteID)
	check           (
					accountID in
						(select id from Student)
					or
					accountID in
						(select id from Administrator)
					)
);

create table Website (
	websiteID		serial,
	title			text,
	primary key		(websiteID)
);

create table Webpage (
	-- todo: depict relationship between website and webpage
	webpageID		serial,
	title			text,
	filename		text,
	contents		text,	-- url to HTML file
					-- possibly add stylesheet and script? idk
	primary key		(webpageID)
);
