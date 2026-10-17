#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/8f93c1170793311e620e13434e0368691d981c0a42a2c972565ee4cae1c91476/contract';
import endContract from '../../snapshots/8f93c1170793311e620e13434e0368691d981c0a42a2c972565ee4cae1c91476/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col, fn, primaryKey, sql } from '@prisma/orm-postgres/migration';

export default class M extends Migration<never, End> {
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createSchema({ schema: 'public' }),
      this.createTable({
        schema: 'public',
        table: 'clients',
        columns: [
          col('email', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'uuid', {
            notNull: true,
            default: fn(sql`gen_random_uuid()`),
            codecRef: { codecId: 'pg/uuid@1' },
          }),
          col('name', 'character varying(400)', {
            notNull: true,
            codecRef: { codecId: 'sql/varchar@1', typeParams: { length: 400 } },
          }),
          col('registered_at', 'timestamptz', {
            notNull: true,
            default: fn(sql`now()`),
            codecRef: { codecId: 'pg/timestamptz-string@1' },
          }),
        ],
        constraints: [primaryKey(['id'], { name: 'clients_pkey' })],
      }),
      this.createTable({
        schema: 'public',
        table: 'contracts',
        columns: [
          col('client_id', 'uuid', { notNull: true, codecRef: { codecId: 'pg/uuid@1' } }),
          col('contract', 'jsonb', { notNull: true, codecRef: { codecId: 'pg/jsonb@1' } }),
          col('id', 'uuid', { notNull: true, codecRef: { codecId: 'pg/uuid@1' } }),
        ],
        constraints: [primaryKey(['id'], { name: 'contracts_pkey' })],
      }),
      this.createTable({
        schema: 'public',
        table: 'security',
        columns: [
          col('client_secret', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'uuid', {
            notNull: true,
            default: fn(sql`gen_random_uuid()`),
            codecRef: { codecId: 'pg/uuid@1' },
          }),
          col('password_hash', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'uuid', { notNull: true, codecRef: { codecId: 'pg/uuid@1' } }),
        ],
        constraints: [primaryKey(['id'], { name: 'security_pkey' })],
      }),
      this.addUnique({
        schema: 'public',
        table: 'clients',
        constraint: 'clients_email_key',
        columns: ['email'],
      }),
      this.addUnique({
        schema: 'public',
        table: 'security',
        constraint: 'security_user_id_key',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'contracts',
        foreignKey: {
          name: 'contracts_client_id_fkey',
          columns: ['client_id'],
          references: { schema: 'public', table: 'clients', columns: ['id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'security',
        foreignKey: {
          name: 'security_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'clients', columns: ['id'] },
        },
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
