-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Хост: vityah1.mysql.ukraine.com.ua
-- Час створення: Вер 07 2021 р., 11:53
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
-- Структура таблиці `myBudj`
--

CREATE TABLE `myBudj` (
  `id` int(11) NOT NULL,
  `cat` varchar(99) COLLATE cp1251_ukrainian_ci NOT NULL,
  `sub_cat` varchar(99) COLLATE cp1251_ukrainian_ci NOT NULL COMMENT 'підкатегорія',
  `mydesc` varchar(150) COLLATE cp1251_ukrainian_ci NOT NULL,
  `suma` int(11) NOT NULL,
  `currencyCode` int(11) NOT NULL DEFAULT '980',
  `mcc` int(11) NOT NULL,
  `rdate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `type_payment` varchar(49) COLLATE cp1251_ukrainian_ci NOT NULL COMMENT 'карта готівка',
  `id_bank` varchar(20) COLLATE cp1251_ukrainian_ci NOT NULL COMMENT 'id операції в банку',
  `owner` varchar(19) COLLATE cp1251_ukrainian_ci NOT NULL COMMENT 'хто джерело витрат',
  `source` varchar(49) COLLATE cp1251_ukrainian_ci NOT NULL COMMENT 'джерело внесення суми',
  `tmp` varchar(20) COLLATE cp1251_ukrainian_ci NOT NULL,
  `deleted` int(1) NOT NULL COMMENT 'чи видалений запис',
  `d_mod_row` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=cp1251 COLLATE=cp1251_ukrainian_ci COMMENT='список витрат';

--
-- Дамп даних таблиці `myBudj`
--

--
-- Індекси збережених таблиць
--

--
-- Індекси таблиці `myBudj`
--
ALTER TABLE `myBudj`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `I_myBudj_id_bank` (`rdate`,`cat`,`sub_cat`,`id_bank`,`suma`,`deleted`) USING BTREE;

--
-- AUTO_INCREMENT для збережених таблиць
--

--
-- AUTO_INCREMENT для таблиці `myBudj`
--
ALTER TABLE `myBudj`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11640;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
