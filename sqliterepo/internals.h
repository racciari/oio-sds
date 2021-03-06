/*
OpenIO SDS sqliterepo
Copyright (C) 2014 Worldine, original work as part of Redcurrant
Copyright (C) 2015 OpenIO, modified as part of OpenIO Software Defined Storage

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 3.0 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library.
*/

#ifndef OIO_SDS__sqliterepo__internals_h
# define OIO_SDS__sqliterepo__internals_h 1

# include <sqlite3.h>

# include <metautils/lib/metautils.h>
# include <RowName.h>
# include <RowField.h>
# include <Row.h>
# include <Table.h>
# include <TableSequence.h>

# ifndef SQLX_MAX_COND
#  define SQLX_MAX_COND 64
# endif

# ifndef SQLX_MAX_BASES
#  define SQLX_MAX_BASES 2048
# endif

# ifndef SQLX_GRACE_DELAY_COOL
#  define SQLX_GRACE_DELAY_COOL 30L
# endif

# ifndef SQLX_GRACE_DELAY_HOT
#  define SQLX_GRACE_DELAY_HOT 300L
# endif

# ifndef SQLX_DELAY_ELECTION_REPLAY
#  define SQLX_DELAY_ELECTION_REPLAY 5L
# endif

/* Timeout for SQLX_REPLICATE requests, in seconds */
#define SQLX_REPLICATION_TIMEOUT 10.0

/* Size of buffer for reading dump file */
#define SQLX_DUMP_BUFFER_SIZE 32768

/* Size of chunks sent to client when doing chunked SQLX_DUMP */
#define SQLX_DUMP_CHUNK_SIZE (8*1024*1024)

/* Page size at database creation (should be multiple of storage block size) */
#define SQLX_DEFAULT_PAGE_SIZE "4096"

#define MEMBER(D)   ((struct election_member_s*)(D))
#define MMANAGER(D) MEMBER(D)->manager
#define MKEY(D)     MEMBER(D)->key
#define MCFG(D)     MMANAGER(D)->config
#define MKEY_S(D)   hashstr_str(MEMBER(D)->key)

#define CONFIG_CHECK(C) do {\
	EXTRA_ASSERT((C) != NULL);\
	EXTRA_ASSERT((C)->get_local_url != NULL); \
	EXTRA_ASSERT((C)->get_peers != NULL); \
	EXTRA_ASSERT((C)->get_version != NULL); \
	EXTRA_ASSERT((C)->mode <= ELECTION_MODE_GROUP); \
} while (0)

#define MANAGER_CHECK(M) do {\
	EXTRA_ASSERT((M) != NULL);\
	EXTRA_ASSERT((M)->lrutree_members != NULL);\
	CONFIG_CHECK((M)->config); \
} while (0)

#define MEMBER_CHECK(M) do {\
	EXTRA_ASSERT(MEMBER(M) != NULL);\
	NAME_CHECK(&(MEMBER(M)->name)); \
	EXTRA_ASSERT(MEMBER(M)->key != NULL);\
	MANAGER_CHECK(MMANAGER(M));\
} while (0)

#define REPO_CHECK(R) do { \
	EXTRA_ASSERT((R) != NULL); \
	EXTRA_ASSERT((R)->schemas != NULL); \
} while (0)

struct sqlx_cache_s;

struct sqlx_repository_s
{
	gchar basedir[512];

	GTree *schemas;

	/* Not owned */
	struct sqlx_cache_s *cache;
	struct election_manager_s *election_manager;

	/* Hooks */
	sqlx_file_locator_f locator;
	gpointer locator_data;

	sqlx_repo_close_hook close_callback;
	gpointer close_callback_data;

	sqlx_repo_open_hook open_callback;
	gpointer open_callback_data;

	sqlx_repo_change_hook change_callback;
	gpointer change_callback_data;

	/* hash for the directory structure */
	guint hash_width;
	guint hash_depth;

	/* Limits for the base's holder */
	guint bases_count;
	guint bases_max;

	enum sqlx_sync_mode_e sync_mode_solo;
	enum sqlx_sync_mode_e sync_mode_repli;

	gboolean flag_autocreate : 1;
	gboolean flag_autovacuum : 1;
	gboolean flag_delete_on : 1;

	gboolean running : 1;
};

void load_statement(sqlite3_stmt *stmt, Row_t *r, Table_t *t);

const gchar * sqlite_op2str(int op);

/* ----------------------------------------------------------------------------
 * Global variables
 * Not to be altered by a regular server. Designed for testing purposes, or for
 * those who know what they are doing.
 * */

/* In the same precision as oio_ext_monotonic_time(), how many TIMESPAN the
 * current thread should wait for the condition in the cache of bases. */
extern gint64 oio_cache_period_cond_wait;

/* In the same precision as oio_ext_monotonic_time(), how many TIMESPAN the
 * current thread should wait for the condition in the cache of bases. */
extern gint64 oio_election_period_cond_wait;

#endif /*OIO_SDS__sqliterepo__internals_h*/
