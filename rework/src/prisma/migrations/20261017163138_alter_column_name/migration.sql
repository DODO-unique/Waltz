/*
  Warnings:

  - You are about to drop the column `user_id` on the `security` table. All the data in the column will be lost.
  - A unique constraint covering the columns `[client_id]` on the table `security` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `client_id` to the `security` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "security" DROP CONSTRAINT "security_user_id_fkey";

-- DropIndex
DROP INDEX "security_user_id_key";

-- AlterTable
ALTER TABLE "security" DROP COLUMN "user_id",
ADD COLUMN     "client_id" UUID NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "security_user_id_key" ON "security"("client_id");

-- AddForeignKey
ALTER TABLE "security" ADD CONSTRAINT "security_user_id_fkey" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
