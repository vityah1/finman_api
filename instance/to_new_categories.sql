insert into categories (id, name, parent_id, ord, is_visible, user_id) 
select id, cat, 0, ord, pok, 1 from myBudj_spr_cat;

--update spr_categories set user_id = 1;

select * from categories;

select * from myBudj_sub_cat;


insert into categories (name, parent_id, ord, is_visible, user_id) 
select sub_cat, id_cat, ord, 1, 1 from myBudj_sub_cat;


select * from myBudj_sub_cat where sub_cat in (select name from categories);

