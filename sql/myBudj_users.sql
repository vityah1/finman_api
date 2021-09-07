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
-- Структура таблиці `myBudj_users`
--

CREATE TABLE `myBudj_users` (
  `id` int(11) NOT NULL,
  `user` varchar(20) COLLATE cp1251_ukrainian_ci NOT NULL,
  `password` varchar(29) COLLATE cp1251_ukrainian_ci NOT NULL,
  `token` varchar(255) COLLATE cp1251_ukrainian_ci NOT NULL,
  `token_d_create` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'дата створення токену',
  `token_d_end` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' COMMENT 'доки дійсний токен'
) ENGINE=MyISAM DEFAULT CHARSET=cp1251 COLLATE=cp1251_ukrainian_ci;

--
-- Дамп даних таблиці `myBudj_users`
--

--
-- Індекси збережених таблиць
--

--
-- Індекси таблиці `myBudj_users`
--
ALTER TABLE `myBudj_users`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT для збережених таблиць
--

--
-- AUTO_INCREMENT для таблиці `myBudj_users`
--
ALTER TABLE `myBudj_users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
