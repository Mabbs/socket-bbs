/*
 Navicat Premium Data Transfer

 Source Server         : 测试
 Source Server Type    : MySQL
 Source Server Version : 50726
 Source Host           : 10.254.159.48:3306
 Source Schema         : bbs

 Target Server Type    : MySQL
 Target Server Version : 50726
 File Encoding         : 65001

 Date: 19/06/2022 01:00:13
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for forum
-- ----------------------------
DROP TABLE IF EXISTS `forum`;
CREATE TABLE `forum`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `desc` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8 COLLATE = utf8_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for post
-- ----------------------------
DROP TABLE IF EXISTS `post`;
CREATE TABLE `post`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL DEFAULT NULL,
  `content` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `author_id` int(11) NOT NULL,
  `parent_post_id` int(11) NOT NULL DEFAULT 0,
  `forum_id` int(11) NOT NULL,
  `time` datetime NOT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `author_id`(`author_id`) USING BTREE,
  INDEX `parent_post_id`(`parent_post_id`) USING BTREE,
  INDEX `forum_id`(`forum_id`) USING BTREE,
  CONSTRAINT `post_ibfk_1` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `post_ibfk_2` FOREIGN KEY (`forum_id`) REFERENCES `forum` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 20 CHARACTER SET = utf8 COLLATE = utf8_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8 COLLATE = utf8_unicode_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
