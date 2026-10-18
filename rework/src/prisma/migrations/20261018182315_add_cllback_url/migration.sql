/*
  Warnings:

  - Added the required column `callback_url` to the `contracts` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "contracts" ADD COLUMN     "callback_url" TEXT NOT NULL;
