create table Account (
	id					serial,
	givenName			text					not null,
	familyName			text					not null,
	username			varchar(20)				not null	unique,
	hashed_password		text					not null,
	registrationDate	timestamp				default		current_timestamp,
	/* salt is username + registrationDate concatenated */
	primary key	(id)
);

create table FullAccount (
	id					serial,
	email				text					not null	unique,
	phone_number		text,
	primary key			(id),
	foreign key			(id)					references	Account(id)
);

create table Student (
	id					serial,
	primary key			(id),
	foreign key			(id)					references	Account(id)
);

create table Administrator (
	id					serial,
	primary key			(id),
	foreign key			(id)					references	Account(id)
);

create table Teaches (
	adminID				serial,
	studentID			serial,
	foreign key			(adminID)				references	Administrator(id),
	foreign key			(studentID)				references	Student(id),
	primary key			(adminID, studentID)
);

create table Guardian (
	id					serial,
	primary key			(id),
	foreign key			(id)					references	Account(id)
);

create table HasChild (
	studentID			serial,
	guardianID			serial,
	foreign key			(studentID)				references	Student(id),
	foreign key			(guardianID)			references	Guardian(id),
	primary key			(studentID, guardianID)
);

create table Viewer (
	id					serial,
	foreign key			(id)				references	Account(id),
	primary key			(id)
);

create table Friendship (
	studentID			serial,
	friendID			serial,
	foreign key			(studentID)				references	Student(id),
	foreign key			(friendID)				references	Account(id),
	primary key			(studentID, friendID)
);

/* a student may be friends with either another student or a viewer */
create function checkFriendship() returns trigger as $$
begin
	if new.friendID in (select id from Student) or (select id from Viewer) then
		return new;
	else
		raise exception 'Friend must be either a student or a viewer';
	end if;
end;
$$ language plpgsql;

create trigger checkFriendship before insert or update on Friendship for each row execute procedure checkFriendship();

create table Website (
	id					serial,
	title				text					not null,
	primary key			(id)
);

create table Webpage (
	id					serial,
	websiteID			serial,
	title				text					not null,
	filename			text					not null,
	-- url to HTML file
	contents			text					not null,
	primary key			(id),
	foreign key			(websiteID)				references	Website(id)
);

create table AdministratorOwnsWebsite (
    administratorID		serial,
    websiteID 			serial,
    foreign key 		(administratorID)		references Administrator(id),
    foreign key			(websiteID)				references Website(id),
    primary key			(administratorID, websiteID)
);

create table StudentOwnsWebsite (
	studentID			serial,
	websiteID			serial,
	foreign key			(studentID)				references	Student(id),
	foreign key			(websiteID)				references	Website(id),
	primary key			(studentID, websiteID)
);

create table CanViewWebsite (
	accountID			serial,
	websiteID			serial,
	foreign key			(accountID)				references	Account(id),
	foreign key			(websiteID)				references	Website(id),
	primary key			(accountID, websiteID)
);

create function checkViewerOfWebsite() returns trigger as $$
begin
	if new.accountID in (select id from Viewer) or (select id from Guardian) then
		return new;
	else
		raise exception 'Additional viewers of a website must be either a guardian or a viewer';
	end if;
end;
$$ language plpgsql;

create trigger checkViewerOfWebsite before insert or update on CanViewWebsite for each row execute procedure checkViewerOfWebsite();