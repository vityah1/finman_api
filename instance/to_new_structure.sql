select * from myBudj where (id_bank,2) in (select id_bank, count(*) from myBudj group by id_bank having count(*) > 1)
order by id_bank;

DELETE FROM myBudj
WHERE id NOT IN (
    SELECT MIN(id)
    FROM myBudj
    GROUP BY rdate,owner,cat,sub_cat,suma,deleted
);


select * from myBudj where (rdate,owner,cat,sub_cat,suma,deleted,3) in 
(select rdate,owner,cat,sub_cat,suma,deleted, count(*) from myBudj group by rdate,owner,cat,sub_cat,suma,deleted having count(*) > 1)
order by rdate,owner,cat,sub_cat,suma,deleted;

INSERT INTO payments (
                         rdate,
                         category_id,
                         description,
                         amount,
                         currencyCode,
                         mcc,
                         type_payment,
                         bank_payment_id,
                         user_id,
                         source,
                         is_deleted,
                         created,
                         updated,
                         mono_user_id
                     )
                     SELECT rdate,
     case 
     when 
     b.sub_cat !="" 
     and 
     b.sub_cat in (select name from categories where parent_id>0) 
     then (select id from categories where name=b.sub_cat and parent_id>0 limit 1)
     when 
     b.mydesc like "Заправка%"
     then (select id from categories where name='Заправка' and parent_id>0 limit 1)     
     when 
     cat !=""
     and 
     b.cat in (select name from categories where parent_id=0)
     then (select id from categories where name=b.cat and parent_id=0 limit 1)
     else (select id from categories where parent_id=0 and name='Інше') 
     end as category_id,
/*     (select id from categories c where c.name=b.cat and c.parent_id=0 limit 1) as cat_id,
     cat,
     (select id from categories c where c.name=b.sub_cat and c.parent_id>0 limit 1) as sub_cat_id,
     sub_cat,*/
     case 
     when sub_cat !="" and sub_cat not in (select name from categories where parent_id>0)
     then sub_cat||case when mydesc !="" then '; '||mydesc else '' end
     else 
       mydesc end as `desc`,
       suma,
       currencyCode,
       mcc,
       case 
       when type_payment = "готівка" then 'cash'
       when type_payment = "CARD" then 'card'
       else 'cash'
       end as type_payment,
       id_bank as bank_payment_id,
       1 as user_id,
       case when source != "" then source else 'pwa' end as source,
       deleted as is_deleted,
       rdate as created,
       d_mod_row as updated,
       case 
       when b.owner='vik' then 1
       when b.owner='tanya' then 2
       else 1
       end as mono_user_id
  FROM myBudj b;
  

select * from categories where parent_id=0;

SELECT rdate,
     case 
     when 
     b.sub_cat !="" 
     and 
     b.sub_cat in (select name from categories where parent_id>0) 
     then (select id from categories where name=b.sub_cat and parent_id>0 limit 1)
     when 
     b.mydesc like "Заправка%"
     then (select id from categories where name='Заправка' and parent_id>0 limit 1)     
     when 
     cat !=""
     and 
     b.cat in (select name from categories where parent_id=0)
     then (select id from categories where name=b.cat and parent_id=0 limit 1)
     else (select id from categories where parent_id=0 and name='Інше') 
     end as category_id,
/*     (select id from categories c where c.name=b.cat and c.parent_id=0 limit 1) as cat_id,
     cat,
     (select id from categories c where c.name=b.sub_cat and c.parent_id>0 limit 1) as sub_cat_id,
     sub_cat,*/
     case 
     when sub_cat !="" and sub_cat not in (select name from categories where parent_id>0)
     then sub_cat||case when mydesc !="" then '; '||mydesc else '' end
     else 
       mydesc end as `desc`,
       suma,
       currencyCode,
       mcc,
       case 
       when type_payment = "готівка" then 'cash'
       when type_payment = "CARD" then 'card'
       else 'cash'
       end as type_payment,
       id_bank as bank_payment_id,
       1 as user_id,
       case when source != "" then source else 'pwa' end as source,
       deleted as is_deleted,
       rdate as created,
       d_mod_row as updated,
       case 
       when b.owner='vik' then 1
       when b.owner='tanya' then 2
       else 1
       end as mono_user_id
  FROM myBudj b;
--   where cat = 'Авто та АЗС';
