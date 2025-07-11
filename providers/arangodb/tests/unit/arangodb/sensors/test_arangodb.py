#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from airflow.models import Connection
from airflow.models.dag import DAG
from airflow.providers.arangodb.sensors.arangodb import AQLSensor
from airflow.utils import timezone

# The tests do not create dag runs, so db isolation tests are skipped

DEFAULT_DATE = timezone.datetime(2017, 1, 1)
arangodb_hook_mock = Mock(name="arangodb_hook_for_test", **{"query.return_value.count.return_value": 1})


class TestAQLSensor:
    @pytest.fixture(autouse=True)
    def setup_connections(self, create_connection_without_db):
        args = {"owner": "airflow", "start_date": DEFAULT_DATE}
        dag = DAG("test_dag_id", schedule=None, default_args=args)
        self.dag = dag
        create_connection_without_db(
            Connection(
                conn_id="arangodb_default",
                conn_type="arangodb",
                host="http://127.0.0.1:8529",
                login="root",
                password="password",
                schema="_system",
            )
        )

    @patch(
        "airflow.providers.arangodb.sensors.arangodb.ArangoDBHook",
        autospec=True,
        return_value=arangodb_hook_mock,
    )
    def test_arangodb_document_created(self, arangodb_mock):
        query = "FOR doc IN students FILTER doc.name == 'judy' RETURN doc"

        arangodb_tag_sensor = AQLSensor(
            task_id="aql_search_document",
            query=query,
            timeout=60,
            poke_interval=10,
            dag=self.dag,
        )

        arangodb_tag_sensor.execute({})
        assert arangodb_hook_mock.query.return_value.count.called
