import unittest
from tests.integration.base_integration import BaseIntegrationTest
from services.table_creator import TableCreator

class TestModelsIntegration(BaseIntegrationTest):
    def test_create_tables_already_exists(self):
        TableCreator().create_tables()

if __name__ == '__main__':
    unittest.main()
