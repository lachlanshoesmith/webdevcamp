do $$ declare
    r record;
begin
    for r in (select tablename from pg_tables where schemaname = 'public') loop
        execute 'drop table if exists ' || quote_ident(r.tablename) || ' cascade';
    end loop;
end $$;


create table Account (
	id					serial,
	given_name			text					not null,
	family_name			text					not null,
	username			varchar(20)				not null	unique,
	hashed_password		text					not null,
	registration_time	timestamp				default		current_timestamp,
	/* salt is username + registration_time concatenated */
	primary key	(id)
);

create table Full_Account (
	id					serial,
	email				text					not null	unique,
	phone_number		text					unique,
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
	administrator_id				serial,
	student_id			serial,
	foreign key			(administrator_id)				references	Administrator(id),
	foreign key			(student_id)				references	Student(id),
	primary key			(administrator_id, student_id)
);

create table Guardian (
	id					serial,
	primary key			(id),
	foreign key			(id)					references	Account(id)
);

create table Has_Child (
	student_id			serial,
	guardian_id			serial,
	foreign key			(student_id)				references	Student(id),
	foreign key			(guardian_id)			references	Guardian(id),
	primary key			(student_id, guardian_id)
);

create table Viewer (
	id					serial,
	foreign key			(id)				references	Account(id),
	primary key			(id)
);

create table Friendship (
	student_id			serial,
	friend_id			serial,
	foreign key			(student_id)				references	Student(id),
	foreign key			(friend_id)				references	Account(id),
	primary key			(student_id, friend_id)
);

/* a student may be friends with either another student or a viewer */
create or replace function check_friendship() returns trigger as $$
begin
	if new.friend_id in (select id from Student) or (select id from Viewer) then
		return new;
	else
		raise exception 'Friend must be either a student or a viewer';
	end if;
end;
$$ language plpgsql;

create or replace trigger check_friendship before insert or update on Friendship for each row execute procedure check_friendship();

create table Website (
	id					serial,
	title				text					not null,
	primary key			(id)
);

create table Webpage (
	id					serial,
	website_id			serial,
	title				text					not null,
	filename			text					not null,
	-- url to HTML file
	contents			text					not null,
	primary key			(id),
	foreign key			(website_id)				references	Website(id)
);

create table Administrator_Owns_Website (
    administrator_id		serial,
    website_id 			serial,
    foreign key 		(administrator_id)		references Administrator(id),
    foreign key			(website_id)				references Website(id),
    primary key			(administrator_id, website_id)
);

create table Student_Owns_Website (
	student_id			serial,
	website_id			serial,
	foreign key			(student_id)				references	Student(id),
	foreign key			(website_id)				references	Website(id),
	primary key			(student_id, website_id)
);

create table Can_View_Website (
	account_id			serial,
	website_id			serial,
	foreign key			(account_id)				references	Account(id),
	foreign key			(website_id)				references	Website(id),
	primary key			(account_id, website_id)
);

create or replace function check_viewer_of_website() returns trigger as $$
begin
	if new.account_id in (select id from Viewer) or (select id from Guardian) then
		return new;
	else
		raise exception 'Additional viewers of a website must be either a guardian or a viewer';
	end if;
end;
$$ language plpgsql;

drop type Full_Account_Type cascade;
create type Full_Account_Type as (id integer, email text, phone_number text, given_name text, family_name text, username varchar(20), registration_time timestamp);

create or replace function get_user_from_email(provided_email text) returns setof Full_Account_Type as $$
begin
	return query (
		select f.id, f.email, f.phone_number, a.given_name, a.family_name, a.username, a.registration_time
		from Full_Account f
		join Account a
		on f.id = a.id
		where email = provided_email
	);
end;
$$ language plpgsql;


create or replace function get_user_from_username(provided_username text) returns setof Full_Account_Type as $$
begin
	if exists (select 1 from Full_Account f join Account a on f.id = a.id where a.username = provided_username) then
		return query (
			select f.id, f.email, f.phone_number, a.given_name, a.family_name, a.username, a.registration_time
			from Full_Account f
			join Account a
			on f.id = a.id
			where username = provided_username
		);
	elsif exists (select 1 from Account where username = provided_username) then 
		return query (
			select id, given_name, family_name, username, registration_time
			from Account a
			where username = provided_username
		);
	end if;
end;
$$ language plpgsql;


create or replace trigger check_viewer_of_website before insert or update on Can_View_Website for each row execute procedure check_viewer_of_website();