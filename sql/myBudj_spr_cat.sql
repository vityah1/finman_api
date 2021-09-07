-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Хост: vityah1.mysql.ukraine.com.ua
-- Час створення: Вер 07 2021 р., 11:50
-- Версія сервера: 5.7.33-36-log
-- Версія PHP: 7.2.34

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База даних: `vityah1_db`
--

-- --------------------------------------------------------

--
-- Структура таблиці `myBudj_spr_cat`
--

CREATE TABLE `myBudj_spr_cat` (
  `id` int(11) NOT NULL,
  `cat` varchar(99) COLLATE cp1251_ukrainian_ci NOT NULL,
  `name` varchar(99) COLLATE cp1251_ukrainian_ci NOT NULL,
  `sub_cat` varchar(49) COLLATE cp1251_ukrainian_ci NOT NULL,
  `ord` int(11) NOT NULL COMMENT 'порядок сортування',
  `pok` int(11) NOT NULL COMMENT 'показувати для ручного внесення'
) ENGINE=MyISAM DEFAULT CHARSET=cp1251 COLLATE=cp1251_ukrainian_ci COMMENT='довідник категорій витрат';

--
-- Дамп даних таблиці `myBudj_spr_cat`
--

INSERT INTO `myBudj_spr_cat` (`id`, `cat`, `name`, `sub_cat`, `ord`, `pok`) VALUES
(2, 'Подорожі', '', '', 100, 1),
(3, 'Краса та медицина', '', '', 60, 1),
(4, 'Розваги та спорт', '', '', 90, 1),
(5, 'Кафе та ресторани', '', '', 40, 1),
(6, 'Продукти й супермаркети', '', '1', 10, 1),
(7, 'Кіно', '', '', 0, 0),
(8, 'Авто та АЗС', '', '1', 50, 1),
(9, 'Одяг і взуття', '', '', 80, 1),
(10, 'Таксі', '', '', 0, 0),
(11, 'Тварини', '', '', 0, 0),
(12, 'Книги', '', '', 0, 0),
(13, 'Квіти', '', '', 0, 0),
(14, 'Поповнення мобільного', '', '', 0, 0),
(15, 'Грошові перекази', '', '', 0, 0),
(16, 'Комунальні послуги', '', '', 0, 0),
(17, 'Інше', '', '', 70, 1),
(18, 'Діти', '', '1', 20, 1),
(19, 'Дружина', '', '1', 30, 1),
(22, 'ДН та іменини', '', '', 75, 1);

--
-- Індекси збережених таблиць
--

--
-- Індекси таблиці `myBudj_spr_cat`
--
ALTER TABLE `myBudj_spr_cat`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `cat` (`cat`);

--
-- AUTO_INCREMENT для збережених таблиць
--

--
-- AUTO_INCREMENT для таблиці `myBudj_spr_cat`
--
ALTER TABLE `myBudj_spr_cat`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
