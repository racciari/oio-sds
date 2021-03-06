import os
import xattr
import mock

from oio.blob.indexer import BlobIndexerWorker
from oio.common.exceptions import FaultyChunk
from oio.rdir.client import RdirClient
from tests.functional.rdir.common import generate_id
from tests.utils import BaseTestCase


class TestIndexerCrawler(BaseTestCase):
    def setUp(self):
        super(TestIndexerCrawler, self).setUp()

        self.namespace = self.conf['namespace']

        self.gridconf = {"namespace": self.namespace}
        self.rdir_client = RdirClient(self.gridconf)

    def tearDown(self):
        super(TestIndexerCrawler, self).tearDown()

    def _create_chunk(self, rawx_path):
        container_id = generate_id(64)
        content_id = generate_id(64)
        chunk_id = generate_id(64)

        chunk_dir = "%s/%s" % (rawx_path, chunk_id[0:2])
        if not os.path.isdir(chunk_dir):
            os.makedirs(chunk_dir)

        chunk_path = "%s/%s" % (chunk_dir, chunk_id)
        with open(chunk_path, "w") as f:
            f.write("toto")

        xattr.setxattr(chunk_path, 'user.grid.chunk.hash', 32 * '0')
        xattr.setxattr(chunk_path, 'user.grid.chunk.id', chunk_id)
        xattr.setxattr(chunk_path, 'user.grid.chunk.position', '0')
        xattr.setxattr(chunk_path, 'user.grid.chunk.size', '4')
        xattr.setxattr(chunk_path, 'user.grid.content.container', container_id)
        xattr.setxattr(chunk_path, 'user.grid.content.id', content_id)
        xattr.setxattr(chunk_path, 'user.grid.content.nbchunk', '1')
        xattr.setxattr(chunk_path, 'user.grid.content.path', 'toto')
        xattr.setxattr(chunk_path, 'user.grid.content.size', '4')
        xattr.setxattr(chunk_path, 'user.grid.content.mime_type',
                                   'application/octet-stream')
        xattr.setxattr(chunk_path, 'user.grid.content.storage_policy',
                                   'TESTPOLICY')
        xattr.setxattr(chunk_path, 'user.grid.content.chunk_method',
                                   'bytes')
        xattr.setxattr(chunk_path, 'user.grid.content.version', '0')

        return chunk_path, container_id, content_id, chunk_id

    def _rdir_get(self, rawx_addr, container_id, content_id, chunk_id):
        data = self.rdir_client.chunk_fetch(rawx_addr)
        key = (container_id, content_id, chunk_id)
        for i_container, i_content, i_chunk, i_value in data:
            if (i_container, i_content, i_chunk) == key:
                return i_value
        return None

    def test_index_chunk(self):
        rawx_conf = self.conf['rawx'][0]

        # create a fake chunk
        chunk_path, container_id, content_id, chunk_id = self._create_chunk(
            rawx_conf['path'])

        # index the chunk
        indexer = BlobIndexerWorker(self.gridconf, None, rawx_conf['path'])

        with mock.patch('oio.blob.indexer.time.time',
                        mock.MagicMock(return_value=1234)):
            indexer.update_index(chunk_path)

        # check rdir
        check_value = self._rdir_get(rawx_conf['addr'], container_id,
                                     content_id, chunk_id)

        self.assertIsNotNone(check_value)

        self.assertEqual(check_value['content_nbchunks'], 1)
        self.assertEqual(check_value['chunk_hash'], 32 * '0')
        self.assertEqual(check_value['content_size'], 4)
        self.assertEqual(check_value['content_path'], 'toto')
        self.assertEqual(check_value['chunk_position'], '0')
        self.assertEqual(check_value['chunk_size'], 4)
        self.assertEqual(check_value['mtime'], 1234)
        self.assertEqual(check_value['content_version'], 0)

        # index a chunk already indexed
        with mock.patch('oio.blob.indexer.time.time',
                        mock.MagicMock(return_value=4567)):
            indexer.update_index(chunk_path)

        # check rdir
        check_value = self._rdir_get(rawx_conf['addr'], container_id,
                                     content_id, chunk_id)

        self.assertIsNotNone(check_value)

        self.assertEqual(check_value['mtime'], 4567)

    def test_index_chunk_missing_xattr(self):
        rawx_conf = self.conf['rawx'][0]

        # create a fake chunk
        chunk_path, container_id, content_id, chunk_id = self._create_chunk(
            rawx_conf['path'])

        # remove mandatory xattr
        xattr.removexattr(chunk_path, 'user.grid.chunk.hash')

        # try to index the chunk
        indexer = BlobIndexerWorker(self.gridconf, None, rawx_conf['path'])

        self.assertRaises(FaultyChunk, indexer.update_index, chunk_path)
