-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Хост: vityah1.mysql.ukraine.com.ua
-- Час створення: Вер 07 2021 р., 11:51
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
-- Структура таблиці `myBudj_sub_cat`
--

CREATE TABLE `myBudj_sub_cat` (
  `id` int(11) NOT NULL,
  `id_cat` int(9) NOT NULL,
  `sub_cat` varchar(49) COLLATE cp1251_ukrainian_ci NOT NULL,
  `name` varchar(99) COLLATE cp1251_ukrainian_ci NOT NULL,
  `ord` int(11) NOT NULL COMMENT 'сортування'
) ENGINE=MyISAM DEFAULT CHARSET=cp1251 COLLATE=cp1251_ukrainian_ci COMMENT='довілник підкатегорій для myBudj_spr_cat';

--
-- Дамп даних таблиці `myBudj_sub_cat`
--

INSERT INTO `myBudj_sub_cat` (`id`, `id_cat`, `sub_cat`, `name`, `ord`) VALUES
(1, 8, 'Заправка', '', 20),
(2, 8, 'Ремонт', '', 30),
(3, 8, 'Мийка', '', 10),
(4, 18, 'Дитина 1', '', 20),
(5, 18, 'Дитина 2', '', 30),
(6, 18, 'Всі', '', 10),
(10, 18, 'Дитина 1 анлійська', '', 20),
(11, 6, 'Базар', '', 10),
(12, 6, 'Пані Анна', '', 10),
(13, 19, 'Косметологія', '', 10),
(14, 19, 'Інше', '', 10),
(15, 19, 'Одяг та взуття', '', 10),
(16, 8, 'Запчастини', '', 30);

--
-- Індекси збережених таблиць
--

--
-- Індекси таблиці `myBudj_sub_cat`
--
ALTER TABLE `myBudj_sub_cat`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT для збережених таблиць
--

--
-- AUTO_INCREMENT для таблиці `myBudj_sub_cat`
--
ALTER TABLE `myBudj_sub_cat`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
