"""
Interface for complex CRUD database request
    Temporarily not support foreign keys
"""
#    Author: Wang Chuhan(wchwzhsgdx@gmail.com)
#    Time: 2021.03.20
#    for Data Manage Platform(TJU CS2018-3)
import json
import pymysql
from dbconn import DBConnector


class SqlCreator(DBConnector):
    """ Create a list recording affairs before commit to MySQL database

    There should be a connection to a database above all
    Provide an interface for complex CRUD database request
    The query operation will expose the dictionary object converted by cursor upward

    Attributions:
    _transaction: a list of transaction before committing

    """

    def __init__(self):
        """ initialization function

        Create an empty list of database transactions

        """
        super().__init__()
        self._transaction = []

    def create_object_sql(self, _json, database_name, table_name):
        """ C(Create) of database data

        Can add multiple data, up to 10000
        The incoming data should be in JSON format
        Add generated sql statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <Data.json> for details
        database_name: String
            name of an existed database
        table_name: String
            name of an existed table of above database

        Returns
        -------
        sql_list: list
            all insert sql_list statements generated by this function

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.create_object_sql('json_str', 'test', 'table1')
        ["INSERT INTO table1(id, name) VALUE(1, 'Jason');", "INSERT INTO table1(id, name) VALUE(2, 'Asuka');",
        "INSERT INTO table1(id, name) VALUE(3, 'Wang');"]

        """
        objects = json.loads(_json)
        assert len(objects) < 10000, u'插入数据太多超出限制！'
        sql_template = 'INSERT INTO %s(%s) VALUE(%s);'
        sql_list = []

        description_list = self.table_columns(database_name, table_name).fetchall()
        fields = []
        for description in description_list:
            fields.append(description['Field'])
        fields_str = ', '.join(fields)

        for _, value in objects.items():
            values = []
            for field in fields:
                if type(value[field]) != int and type(value[field]) != float:
                    value[field] = "'" + value[field] + "'"
                values.append(str(value[field]))
            values_str = ', '.join(values)
            sql_list.append(sql_template % (database_name + '.' + table_name, fields_str, values_str))

        self._transaction = self._transaction + sql_list
        return sql_list

    def retrieve_object_sql(self, _json, database_name, table_name):
        """ R(Retrieve) the selected column of the selected table in the selected database

        The incoming data should be in JSON format
        Returns the dictionary object converted by cursor upward

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <Data.json> for details
        database_name: String
            name of an existed database
        table_name: String
            name of an existed table of above database

        Returns
        -------
        sql_list: String
            a list of sql_list contains sql_list statement: 'SELECT [columns] FROM [database_name]'
        dic: dict
            a dictionary of retrieve result

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.retrieve_object_sql('json_str', 'test', 'table2')
        ['SELECT Host, Db, User FROM db;']

        Notes
        -----
        if JSON file have key 'Limit', it will limit the number of data read out
        if JSON file have key 'Start', it will set start location of reading out
        if JSON file only have key 'Start' without 'Limit', 'Start' config will not work

        """
        sql_template = 'SELECT %s FROM %s'
        sql_list = []

        fields = json.loads(_json)
        columns = fields['Fields']
        columns_str = ', '.join(columns)
        try:
            sql_list.append((sql_template % (columns_str, database_name + '.' + table_name)) +
                            (' LIMIT %d, %d' % (fields['Start'], fields['Limit'])) + ';')
        except KeyError:
            try:
                sql_list.append((sql_template % (columns_str, database_name + '.' + table_name))
                                + ('LIMIT 0, %d' % fields['Limit']) + ';')
            except KeyError:
                sql_list.append(sql_template % (columns_str, database_name + '.' + table_name) + ';')

        dic = {}
        try:
            dic = self.execute_sql(sql_list[0]).fetchall()
        except pymysql.err.Error:
            print('查询数据出错，请修改后尝试！')

        return sql_list, dic

    def update_object_sql(self, _json, database_name, table_name):
        """ U(Update) the data of the selected table in the selected database

        Can update multiple data, up to 10000
        The incoming data should be in JSON format
        Add generated sql statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <UpdateDate.json> for details
        database_name: String
            name of an existed database
        table_name: String
            name of an existed table of above database

        Returns
        -------
        sql_list: list
            all update sql_list statements generated by this function

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.update_object_sql('json_str', 'test', 'table2')
        ['UPDATE table1 SET password=456 WHERE id=1;', "UPDATE table1 SET name='Alice' WHERE id=2;",
         "UPDATE table1 SET name='White', password=123 WHERE id=3;"]

        """
        objects = json.loads(_json)
        assert len(objects) < 10000, u'修改数据太多超出限制！'
        description_list = self.table_columns(database_name, table_name).fetchall()
        sql_template = 'UPDATE %s SET %s WHERE %s;'
        sql_list = []

        primary_key = ''
        for description in description_list:
            if description['Key'] == 'PRI':
                primary_key = description['Field']

        for _, value in objects.items():
            modify_attr = value["update"]
            key_value = []
            for attr in modify_attr:
                if type(value[attr]) != int and type(value[attr]) != float:
                    value[attr] = "'" + str(value[attr]) + "'"
                key_value.append(attr + '=' + str(value[attr]))
            key_value_str = ', '.join(key_value)
            sql_list.append(sql_template % (database_name + '.' + table_name, key_value_str,
                                            primary_key + "=" + str(value[primary_key])))

        self._transaction = self._transaction + sql_list
        return sql_list

    def delete_object_sql(self, _json, database_name, table_name):
        """ D(Delete) selected data of the selected table in the selected database

        Can delete multiple data, up to 10000
        The incoming data should be in JSON format
        Add generated sql_list statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <DeleteData.json> for details
        database_name: String
            name of an existed database
        table_name: String
            name of an existed table of above database

        Returns
        -------
        sql_list: list
            all delete sql_list statements generated by this function

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.delete_object_sql('json_str', 'test', 'table1')
        ['DELETE FROM table2 WHERE id=4;', 'DELETE FROM table2 WHERE id=5;', 'DELETE FROM table2 WHERE id=6;']

        Notes
        -----
        The table using this function should have a primary key.
        Otherwise, using the all columns of the table as the primary key which may cause unexpected errors

        """
        description_list = self.table_columns(database_name, table_name).fetchall()
        objects = json.loads(_json)
        assert len(objects) < 10000, u'修改数据太多超出限制！'
        sql_template = 'DELETE FROM %s WHERE %s'
        sql_list = []

        primary_key = ''
        for description in description_list:
            if description['Key'] == 'PRI':
                primary_key = description['Field']

        if primary_key == '':
            print('该数据库中没有主键，使用其所有属性值作为索引使用，可能会有预料之外的错误。')
            for _, value in objects.items():
                cond_str = ''
                for k, v in value.items():
                    cond_str = cond_str + '%s=%s, ' % (k, v)
                sql_list.append((sql_template % (database_name + '.' + table_name, cond_str)).rstrip(', ') + ';')
        else:
            for _, value in objects.items():
                sql_list.append(sql_template % (database_name + '.' + table_name,
                                                primary_key + "=" + str(value[primary_key])) + ';')

        self._transaction = self._transaction + sql_list
        return sql_list

    def create_table_sql(self, _json, database_name):
        """ C(Create) of table in database

        The incoming data should be in JSON format
        Add generated sql_list statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <TableData.json> for details
        database_name: String
            name of an existed database

        Returns
        -------
        sql_list: list
            a list contains create table sql statements

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.create_table_sql('json_str', 'test', 'table3')
        ['CREATE TABLE table3(
              id INT PRIMARY KEY NOT NULL DEFAULT NULL,
              time DATE DEFAULT NULL,
              value FLOAT DEFAULT NULL
          );']

        """
        objects = json.loads(_json, )
        sql_template = 'CREATE TABLE %s(%s);'
        sql_list = []

        table_name = ''
        field_str = ''
        for key, value in objects.items():
            table_name = key
            fields = []
            for _, field in value.items():
                attr_str = field['Field'] + ' ' + field['Type']

                if field['Key'] == 'PRI':
                    attr_str = attr_str + ' PRIMARY KEY'

                try:
                    if field['Null'] == 'NO':
                        attr_str = attr_str + ' NOT NULL'
                except KeyError:
                    pass

                try:
                    if field['Default'] == 'NULL':
                        attr_str = attr_str + ' DEFAULT NULL'
                    elif type(field['Default']) != int and type(field['Default']) != float:
                        attr_str = attr_str + " '" + field['Default'] + "'"
                    else:
                        attr_str = attr_str + ' ' + field['Default']
                except KeyError:
                    pass

                fields.append(attr_str)
                field_str = ', '.join(fields)

        sql_list.append(sql_template % (database_name + '.' + table_name, field_str))
        self._transaction = self._transaction + sql_list
        return sql_list

    def retrieve_table_sql(self, _json, database_name):
        """ R(Retrieve) the selected table in the selected database

        The incoming data should be in JSON format
        Returns the dictionary object converted by cursor upward

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <retrieveData.json> for details
        database_name: String
            name of an existed database

        Returns
        -------
        sql_list: String
            a list of sql_list contains sql statement: 'DESC [table_name]'
        dic: dict
            a dictionary of retrieve result

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.retrieve_table_sql('json_str', 'test')
        ['DESC table2']

        """
        objects = json.loads(_json)
        assert len(objects) == 1, u'输入的查询对象没有意义！'
        sql_template = 'DESC %s'
        sql_list = []

        dic = {}
        try:
            sql_list.append(sql_template % database_name + '.' + objects['table'])
            dic = self.execute_sql(sql_list[0]).fetchall()
        except pymysql.err.Error:
            print('查询操作出错，请修改后重试')

        return sql_list, dic

    def update_table_sql(self, _json, database_name):
        """ U(Update) columns of table in selected database

        The incoming data should be in JSON format
        Add generated sql_list statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <UpdateTable.json> for details
        database_name: String
            name of an existed database

        Returns
        -------
        sql_list: list
            a list contains all update table sql statements generated by this function

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.update_table_sql('json_str', 'test')
        ['ALTER TABLE table3 ADD char CHAR(5) DEFAULT NULL;', 'ALTER TABLE table3 DROP COLUMN value;',
         'ALTER TABLE table3 MODIFY time TIME;']

        Notes
        -----
        the "Alter" key should be used in each attribute of the JSON file to indicate the update type
        if "Alter" key is "add", it will add a column to table which attributes are marked in JSON file
        if "Alter" key is "modify", it will modify this column in table
        if "Alter" key is "drop", it will delete this column

        """
        objects = json.loads(_json)
        sql_template = 'ALTER TABLE %s %s %s;'
        sql_list = []

        for key, value in objects.items():
            table_name = key
            for _, field in value.items():
                if field['Alter'] == 'add':
                    attr_str = field['Field'] + ' ' + field['Type']
                    if field['Null'] == 'NO':
                        attr_str = attr_str + ' NOT NULL'
                    if field['Default'] == 'NULL':
                        attr_str = attr_str + ' DEFAULT NULL'
                    sql_list.append(sql_template % (database_name + '.' + table_name, 'ADD', attr_str))
                elif field['Alter'] == 'modify':
                    attr_str = field['Field'] + ' ' + field['Type']
                    sql_list.append(sql_template % (database_name + '.' + table_name, 'MODIFY', attr_str))
                elif field['Alter'] == 'drop':
                    attr_str = field['Field']
                    sql_list.append(sql_template % (database_name + '.' + table_name, 'DROP COLUMN', attr_str))
                else:
                    attr_str = field['Alter']
                    raise TypeError('不支持的修改类型%s！' % attr_str)

        self._transaction = self._transaction + sql_list
        return sql_list

    def delete_table_sql(self, _json, database_name):
        """ D(Delete) tables in database

        The incoming data should be in JSON format
        Add generated sql_list statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <DeleteTable.json> for details
        database_name: String
            name of an existed database

        Returns
        -------
        sql_list: list
            a list contains all delete table sql statements generated by this function

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.delete_table_sql('json_str', 'test')
        ['DROP TABLE table1;', 'DROP TABLE table2;', 'DROP TABLE table3;']

        """
        objects = json.loads(_json)
        sql_template = 'DROP TABLE %s;'
        sql_list = []

        for _, value in objects['table'].items():
            sql_list.append(sql_template % database_name + '.' + value)

        self._transaction = self._transaction + sql_list
        return sql_list

    def create_database_sql(self, _json):
        """ C(Create) a new database

        The incoming data should be in JSON format
        Add generated sql_list statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <DatabaseData.json> for details

        Returns
        -------
        sql_list: list
            a list contains create table sql statements

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.create_database_sql('json_str')
        ['CREATE DATABASE test;']

        Notes
        -----
        "charset" key can be used to specify the character set used by the database
            such as "charset": "utf8" can set charset as "utf8"

        """
        objects = json.loads(_json)
        sql_template = 'CREATE DATABASE %s %s'
        sql = []

        database_name = objects['database']
        try:
            charset = "CHARSET='" + objects['charset'] + "';"
        except KeyError:
            charset = ';'
        sql.append(sql_template % (database_name, charset))

        self._transaction = self._transaction + sql
        return sql

    def retrieve_database_sql(self, _json):
        """ R(Retrieve) selected database

        The incoming data should be in JSON format
        Add generated sql_list statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <DatabaseData.json> for details

        Returns
        -------
        sql_list: String
            a list of sql_list contains sql statement: 'SHOW CREATE DATABASE [database_name]'
        dic: dict
            a dictionary of retrieve result

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.retrieve_database_sql('json_str')
        ['SHOW CREATE DATABASE test;']

        """
        sql_template = 'SHOW CREATE DATABASE %s;'
        objects = json.loads(_json)
        dic = {}
        sql_list = []
        try:
            sql_list.append(sql_template % objects['database'])
            dic = self.execute_sql(sql_template % objects['database']).fetchall()
        except pymysql.err.ProgrammingError:
            print("数据库'%s'不存在！" % objects['database'])

        return sql_list, dic

    def update_database_sql(self, _json):
        """  U(Update) database

        The incoming data should be in JSON format
        Add generated sql_list statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <DatabaseData.json> for details

        Returns
        -------
        sql_list: String
            a list of sql_list contains all sql statements generated by this function

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.update_database_sql('json_str')
        ["ALTER DATABASE test CHARSET='utf8'"]

        Notes
        -----
        only character encoding modification is supported

        """
        objects = json.loads(_json)
        sql_template = "ALTER DATABASE %s CHARSET='%s'"
        sql_list = [sql_template % (objects['database'], objects['charset'])]

        self._transaction = self._transaction + sql_list
        return sql_list

    def delete_database_sql(self, _json):
        """ D(Delete) a database

        The incoming data should be in JSON format
        Add generated sql_list statements to enter database transaction list

        Parameters
        ----------
        _json: String
            a string in JSON, refer to document <DatabaseData.json> for details

        Returns
        -------
        sql_list: String
            a list of sql_list contains all sql statements generated by this function

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.delete_database_sql('json_str')
        ['DROP DATABASE test;']

        """
        objects = json.loads(_json)
        sql_template = 'DROP DATABASE %s;'
        sql_list = []
        for database in objects['database']:
            sql_list.append(sql_template % database)

        self._transaction = self._transaction + sql_list
        return sql_list

    def rollback(self, step, reverse=False):
        """ rollback sql statements in retrieve

        Parameters
        ----------
        step: int
            The number of steps in the rollback operation
        reverse: Boolean
            Order of roll_list presentation

        Returns
        -------
        roll_list: list
            The operation of backing out(reverse order default)

        Examples
        --------
        >>> sc = SqlCreator()
        >>> sc.rollback(2)
        ['DROP DATABASE test;', "ALTER DATABASE test CHARSET='utf8'"]

        """
        roll_list = []
        for i in range(step):
            try:
                roll_list.append(self._transaction.pop())
            except IndexError:
                print('已经没有操作可以回退了！')

        if reverse is True:
            return list(reversed(roll_list))
        else:
            return roll_list

    def show_sql_transaction(self):
        """ Get the current database transaction list

        Returns
        -------
        self._transaction: list
            the current database transaction list

        """
        return self._transaction

    def commit_all(self):
        """ Submit the current database transaction list to the database

        CUD operations will first enter the transaction list cache, and then run the function

        Returns
        -------
        status: String
            The number of sql statements executed and total sql statements: (<executed>-<total>)

        Notes
        -----
        Be sure to execute this function

        """
        count = 0
        total = len(self._transaction)
        for affair in self._transaction:
            count = count + 1
            try:
                self.commit_sql(affair)
            except pymysql.err.Error:
                self.rollback(1)
                count = count - 1
                print("Sql Error: %s 语句存在错误，并没有被执行！" % affair)

        self._transaction.clear()
        status = str(count) + '-' + str(total)
        return status


# # 测试用代码，去掉注释使用
# if __name__ == '__main__':
#     config = open('DBData.json')
#     SqlCreator.init_config(json.load(config))
#     sc = SqlCreator()
#     sc.connect_db()
#     text1 = open('Data.json')
#     print(sc.create_object_sql(text1, 'test', 'table1'))
#     text2 = open('Fields.json')
#     sql1, cur1 = sc.retrieve_object_sql(text2, 'mysql', 'db')
#     print(sql1)
#     text3 = open('UpdateData.json')
#     print(sc.update_object_sql(text3, 'test', 'table1'))
#     text4 = open('DeleteData.json')
#     print(sc.delete_object_sql(text4, 'test', 'table2'))
#     text5 = open('TableData.json')
#     print(sc.create_table_sql(text5, 'test'))
#     text12 = open('retrieveData.json')
#     sql2, cur2 = sc.retrieve_table_sql(text12, 'test')
#     print(sql2)
#     text6 = open('UpdateTable.json')
#     print(sc.update_table_sql(text6, 'test'))
#     text7 = open('DeleteTable.json')
#     print(sc.delete_table_sql(text7, 'test'))
#     text8 = open('DatabaseData.json')
#     print(sc.create_database_sql(text8))
#     text13 = open('DatabaseData.json')
#     sql3, cur3 = sc.retrieve_database_sql(text13)
#     print(sql3)
#     text9 = open('UpdateDB.json')
#     print(sc.update_database_sql(text9))
#     text10 = open('DeleteDB.json')
#     print(sc.delete_database_sql(text10))
#
#     print(sc.show_sql_transaction())
#     print(sc.rollback(2, reverse=True))
#     print(sc.show_sql_transaction())
#
#     print(sc.commit_all())
