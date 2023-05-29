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


select * from payments where bank_payment_id = 'doMFEu_RC5HgiKx9-3';
select * from categories;

select * from myBudj where cat = 'Поповнення мобільного';

select * from myBudj where sub_cat = 'Заправка' and rdate > '2023-01-01';
select * from payments where rdate > '2023-01-01' and category_id in (select id from categories where name = 'Заправка');

select p.id, p.rdate, p.category_id, c.name, p.description, p.amount from `payments` p 
left join categories c on p.category_id = c.id
where 1=1  and p.rdate >= '2023-01-22' order by `amount` desc;

select * from config;

SELECT config.value_data AS config_value_data, config.add_value AS config_add_value 
FROM config 
WHERE config.user_id = 1 AND config.type_data = 'phone_to_name';

select p.id, p.rdate, p.category_id,
case
    when c.parent_id = 0 then c.name
    else (select name from categories where id=c.parent_id)
end as name_category
, c.parent_id, p.description, p.amount
from `payments` p left join categories c on p.category_id = c.id
where 1=1 and p.is_deleted = 0
 and p.`rdate` >= '2023-01-01' and p.`rdate` < '2023-02-01'  
-- and p.`category_id` = 14
order by `amount` desc;

select strftime('%Y', `rdate`) as year, CAST(sum(`amount`) AS INTEGER) as amount, count(*) as cnt
from `payments`
where 1=1
and `user_id` = 1 and `is_deleted` = 0 and `amount` > 0
group by strftime('%Y', `rdate`) order by 1 desc;

select strftime('%m', `rdate`) as month, CAST(sum(`amount`) AS INTEGER) as amount, count(*) as cnt
from `payments`
where 1=1 and strftime('%Y', `rdate`) = '2023'
group by strftime('%m', `rdate`) order by 1 desc;