-- RenameForeignKey
ALTER TABLE "security" RENAME CONSTRAINT "security_user_id_fkey" TO "security_client_id_fkey";

-- RenameIndex
ALTER INDEX "security_user_id_key" RENAME TO "security_client_id_key";
