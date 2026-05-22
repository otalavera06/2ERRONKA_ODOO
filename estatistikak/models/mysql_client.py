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

    # DEFAULT_HOST = 'localhost'
    # DEFAULT_PORT = 3306
    # DEFAULT_DATABASE = 'erronka2026'
    # DEFAULT_USER = 'root'
    # DEFAULT_PASSWORD = 'abc123ABC'
    DEFAULT_HOST = 'host.docker.internal'
    DEFAULT_PORT = 3306
    DEFAULT_DATABASE = 'erronka2026'
    DEFAULT_USER = 'root'
    DEFAULT_PASSWORD = '1mg2024'

    def __init__(self, env):
        self.env = env

    def get_eskaerak_with_totals(self):
        query = """
            SELECT
                z.id,
                z.data,
                z.mahaiak_id,
                COALESCE(f.prezio_totala, z.prezioTotala, e.prezio_totala, 0) AS zenbatekoa
                COALESCE(e.prezio_totala, z.prezioTotala, f.prezio_totala, 0) AS zenbatekoa,
                COALESCE(e.produktu_kopurua, 0) AS produktu_kopurua,
                COALESCE(e.plater_kopurua, 0) AS plater_kopurua
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
                SELECT
                    e.zerbitzua_id,
                    SUM(
                        CASE
                            WHEN e.produktua_id = 1 THEN COALESCE(pl.prezioa, e.prezioa, 0)
                            ELSE COALESCE(pr.prezioa, e.prezioa, 0)
                        END
                    ) AS prezio_totala,
                    SUM(CASE WHEN e.produktua_id = 1 THEN 0 ELSE 1 END) AS produktu_kopurua,
                    SUM(CASE WHEN e.produktua_id = 1 THEN 1 ELSE 0 END) AS plater_kopurua
                FROM eskaerak e
                LEFT JOIN produktuak pr ON pr.id = e.produktua_id
                LEFT JOIN platerak pl ON e.produktua_id = 1 AND pl.izena = e.izena
                GROUP BY e.zerbitzua_id
            ) e ON e.zerbitzua_id = z.id
            ORDER BY z.data DESC, z.id DESC
        """
        return self._fetchall(query)

    def get_platerak(self):
        return self._fetchall("""
            SELECT id, izena, mota, prezioa, argazkia
            FROM platerak
            ORDER BY id
        """)

    def create_platera(self, values):
        query = """
            INSERT INTO platerak (izena, mota, prezioa, argazkia)
            VALUES (%s, %s, %s, %s)
        """
        return self._execute(query, (
            values.get('izena'),
            values.get('mota'),
            values.get('prezioa'),
            values.get('argazkia'),
        ), return_lastrowid=True)

    def update_platera(self, mysql_id, values):
        query = """
            UPDATE platerak
            SET izena = %s, mota = %s, prezioa = %s, argazkia = %s
            WHERE id = %s
        """
        self._execute(query, (
            values.get('izena'),
            values.get('mota'),
            values.get('prezioa'),
            values.get('argazkia'),
            mysql_id,
        ))

    def delete_platera(self, mysql_id):
        self._execute("DELETE FROM platerak WHERE id = %s", (mysql_id,))

    def get_langileak(self):
        return self._fetchall("""
            SELECT id, izena, abizena, erabiltzailea, pasahitza, email,
                   telefonoa, baimena, mahaiak_id, chat_baimena
            FROM langileak
            ORDER BY id
        """)

    def create_langilea(self, values):
        query = """
            INSERT INTO langileak
                (izena, abizena, erabiltzailea, pasahitza, email, telefonoa,
                 baimena, mahaiak_id, chat_baimena)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._execute(query, (
            values.get('izena'),
            values.get('abizena'),
            values.get('erabiltzailea'),
            values.get('pasahitza'),
            values.get('email'),
            values.get('telefonoa'),
            values.get('baimena'),
            values.get('mahaiak_id'),
            values.get('chat_baimena'),
        ), return_lastrowid=True)

    def update_langilea(self, mysql_id, values):
        query = """
            UPDATE langileak
            SET izena = %s, abizena = %s, erabiltzailea = %s, pasahitza = %s,
                email = %s, telefonoa = %s, baimena = %s, mahaiak_id = %s,
                chat_baimena = %s
            WHERE id = %s
        """
        self._execute(query, (
            values.get('izena'),
            values.get('abizena'),
            values.get('erabiltzailea'),
            values.get('pasahitza'),
            values.get('email'),
            values.get('telefonoa'),
            values.get('baimena'),
            values.get('mahaiak_id'),
            values.get('chat_baimena'),
            mysql_id,
        ))

    def delete_langilea(self, mysql_id):
        self._execute("DELETE FROM langileak WHERE id = %s", (mysql_id,))

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

    def _execute(self, query, params=None, return_lastrowid=False):
        connection = self._connect()
        cursor = None
        try:
            cursor = self._cursor(connection)
            cursor.execute(query, params or ())
            connection.commit()
            if return_lastrowid:
                return cursor.lastrowid
        except Exception as exc:
            connection.rollback()
            _logger.exception("Could not write data to MySQL.")
            raise UserError("Ezin izan da MySQL datu-basea eguneratu: %s" % exc)
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
