CREATE DATABASE IF NOT EXISTS foodshare;

CREATE TABLE IF NOT EXISTS `cart` (
  `userid` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `restid` int(11) UNSIGNED NOT NULL,
  `itemid` int(11) UNSIGNED NOT NULL,
  `quantity` int(2) UNSIGNED NOT NULL
);

CREATE TABLE IF NOT EXISTS `contactformresponses` (
  `responseid` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `submittedat` bigint(20) NOT NULL,
  `email` varchar(50) NOT NULL,
  `fname` varchar(50) NOT NULL,
  `lname` varchar(50) NOT NULL,
  `nature` enum('Query','Suggestion','Complaint','Feedback','Other') NOT NULL,
  `message` varchar(1000) NOT NULL
);

CREATE TABLE IF NOT EXISTS `fooditems` (
  `itemid` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `restid` int(11) UNSIGNED NOT NULL,
  `inmenu` tinyint(1) NOT NULL DEFAULT 0,
  `name` varchar(100) NOT NULL,
  `description` varchar(200) NOT NULL,
  `price` decimal(5,2) UNSIGNED NOT NULL,
  `restrictions` varchar(100) DEFAULT NULL,
  `picture` varchar(110) NOT NULL DEFAULT 'defaultitem.png'
);

CREATE TABLE IF NOT EXISTS `orders` (
  `orderid` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `ordertime` bigint(20) NOT NULL,
  `userid` int(11) UNSIGNED NOT NULL,
  `restid` int(11) UNSIGNED NOT NULL,
  `orderstatus` enum('Preparing','Ready','Collected') NOT NULL DEFAULT 'Preparing',
  `items` longtext NOT NULL CHECK (json_valid(`items`)),
  `amount` decimal(5,2) UNSIGNED NOT NULL
);

CREATE TABLE IF NOT EXISTS `restaurants` (
  `restid` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `userid` int(11) UNSIGNED NOT NULL,
  `name` varchar(100) NOT NULL,
  `address` varchar(500) NOT NULL,
  `latitude` decimal(8,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  `coverpic` varchar(205) NOT NULL DEFAULT 'defaultcover.png',
  `open` tinyint(1) NOT NULL DEFAULT 0,
  `avgreview` decimal(2,1) UNSIGNED DEFAULT NULL,
  `numreviews` int(10) UNSIGNED NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS `reviews` (
  `reviewid` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `submittedat` bigint(16) NOT NULL,
  `userid` int(11) UNSIGNED NOT NULL,
  `restid` int(11) UNSIGNED NOT NULL,
  `orderid` int(11) UNSIGNED NOT NULL,
  `stars` tinyint(1) UNSIGNED NOT NULL,
  `title` varchar(100) NOT NULL,
  `description` varchar(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS `users` (
  `userid` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `email` varchar(50) NOT NULL,
  `fname` varchar(50) NOT NULL,
  `lname` varchar(50) NOT NULL,
  `hashed_password` varbinary(64) NOT NULL,
  `salt` binary(64) NOT NULL,
  `address` varchar(500) NOT NULL,
  `latitude` decimal(8,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  `reset_id` bigint(16) UNSIGNED DEFAULT NULL,
  `reset_expiry` bigint(16) DEFAULT NULL
);
