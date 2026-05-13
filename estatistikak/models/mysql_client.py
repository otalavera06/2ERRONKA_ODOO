# -*- coding: utf-8 -*-
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import mysql.connector as mysql_connector
except ImportError:
    mysql_connector = None

try:
    import pymysql
except ImportError:
    pymysql = None


class EskaerakMySQLClient:
    """MySQL client for the restaurant statistics used by the Odoo module."""

    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 3306
    DEFAULT_DATABASE = 'erronka2026'
    DEFAULT_USER = 'root'
    DEFAULT_PASSWORD = 'abc123ABC'

    def __init__(self, env):
        self.env = env

    def get_eskaerak_with_totals(self):
        query = """
            SELECT
                z.id,
                z.data,
                z.mahaiak_id,
                COALESCE(f.prezio_totala, z.prezioTotala, e.prezio_totala, 0) AS zenbatekoa
            FROM zerbitzua z
            LEFT JOIN (
                SELECT zerbitzua_id, SUM(prezio_totala) AS prezio_totala
                FROM fakturak
                GROUP BY zerbitzua_id
            ) f ON f.zerbitzua_id = z.id
            LEFT JOIN (
                SELECT zerbitzua_id, SUM(prezioa) AS prezio_totala
                FROM eskaerak
                GROUP BY zerbitzua_id
            ) e ON e.zerbitzua_id = z.id
            ORDER BY z.data DESC, z.id DESC
        """
        return self._fetchall(query)

    def _fetchall(self, query, params=None):
        connection = self._connect()
        cursor = None
        try:
            cursor = self._cursor(connection)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as exc:
            _logger.exception("Could not fetch statistics from MySQL.")
            raise UserError("Ezin izan da MySQL datu-basetik estatistikarik lortu: %s" % exc)
        finally:
            if cursor:
                cursor.close()
            connection.close()

    def _connect(self):
        config = self._config()
        try:
            if mysql_connector:
                return mysql_connector.connect(
                    host=config['host'],
                    port=config['port'],
                    user=config['user'],
                    password=config['password'],
                    database=config['database'],
                    connection_timeout=10,
                )
            if pymysql:
                return pymysql.connect(
                    host=config['host'],
                    port=config['port'],
                    user=config['user'],
                    password=config['password'],
                    database=config['database'],
                    connect_timeout=10,
                    cursorclass=pymysql.cursors.DictCursor,
                )
        except Exception as exc:
            _logger.exception("Could not connect to MySQL.")
            raise UserError("Ezin da MySQLera konektatu: %s" % exc)

        raise UserError(
            "MySQL konektorea falta da. Instalatu `mysql-connector-python` edo `PyMySQL` "
            "Odoo erabiltzen ari den Python ingurunean."
        )

    def _cursor(self, connection):
        try:
            return connection.cursor(dictionary=True)
        except TypeError:
            return connection.cursor()

    def _config(self):
        params = self.env['ir.config_parameter'].sudo()
        return {
            'host': params.get_param('estatistikak.mysql_host') or self.DEFAULT_HOST,
            'port': int(params.get_param('estatistikak.mysql_port') or self.DEFAULT_PORT),
            'database': params.get_param('estatistikak.mysql_database') or self.DEFAULT_DATABASE,
            'user': params.get_param('estatistikak.mysql_user') or self.DEFAULT_USER,
            'password': params.get_param('estatistikak.mysql_password') or self.DEFAULT_PASSWORD,
        }
