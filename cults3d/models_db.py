import sqlite3
import pandas as pd
import os


class Model:
    def __init__(self, url, model_code, barcode, name_en, name_tr, description_en, description_tr, template_description_en, template_description_tr, total_price, volume, status, stl_size):
        self.url = url
        self.model_code = model_code
        self.barcode = barcode
        self.name_en = name_en
        self.name_tr = name_tr
        self.description_en = description_en
        self.description_tr = description_tr
        self.template_description_en = template_description_en
        self.template_description_tr = template_description_tr
        self.total_price = total_price
        self.volume = volume
        self.status = status
        self.stl_size = stl_size


    def __str__(self):
        return (
            f'Link: {self.url}\n'
            f'Model Code: {self.model_code}\n'
            f'Barcode: {self.barcode}\n'
            f'Model Name (EN): {self.name_en}\n'
            f'Model Name (TR): {self.name_tr}\n'
            f'Description (EN):\n {self.description_en}\n'
            f'Description (TR):\n {self.description_tr}\n'
            f'TemplateDescriptionEN:\n {self.template_description_en}\n'
            f'TemplateDescriptionTR:\n {self.template_description_tr}\n'
            f'TotalPrice: {self.total_price}\n'
            f'Volume: {self.volume}\n'
            f'Status: {self.status}\n'
            f'Size1: {self.stl_size}\n'
        )


class ModelDB:
    def __init__(self, db: str, table: str):
        self.db = db
        self.table = table
        self.create_connection()


    def create_connection(self):
        query = f'''
        CREATE TABLE IF NOT EXISTS {self.table} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Link TEXT NOT NULL, 
            Code TEXT UNIQUE NOT NULL, 
            Barcode TEXT UNIQUE NOT NULL,
            NameEN TEXT, 
            NameTR TEXT, 
            DescriptionEN TEXT, 
            DescriptionTR TEXT,
            TemplateDescriptionEN TEXT,
            TemplateDescriptionTR TEXT,
            TotalPrice TEXT, 
            Volume TEXT,
            Status TEXT, 
            Size1 TEXT
        )'''
        self.connection = sqlite3.connect(self.db)
        self.cursor = self.connection.cursor()
        self.cursor.execute(query)
        self.connection.commit()


    def disconnect(self):
        self.connection.close()


    def add_model(self, model: Model):
        query = f'''
        INSERT INTO {self.table} (Link, Code, Barcode, NameEN, NameTR, DescriptionEN, DescriptionTR, TemplateDescriptionEN, TemplateDescriptionTR, TotalPrice, Volume, Status, Size1)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        try:
            self.cursor.execute(query, (
                model.url, model.model_code, model.barcode, model.name_en, model.name_tr,
                model.description_en, model.description_tr, model.template_description_en, model.template_description_tr, model.total_price,
                model.volume, model.status, model.stl_size
            ))
            self.connection.commit()
            print(f'Model {model.model_code} added successfully!')
        except sqlite3.IntegrityError as e:
            print(f'Error: {e}')


    def delete_model(self, model_code: str):
        query = f'DELETE FROM {self.table} WHERE Code = ?'
        self.cursor.execute(query, (model_code,))
        self.connection.commit()
        print(f'Model with Code {model_code} deleted successfully!')


    def check_model(self, model_code: str):
        query = f'SELECT * FROM {self.table} WHERE Code = ?'
        self.cursor.execute(query, (model_code,))
        models = self.cursor.fetchall()
        return len(models) > 0


    def show_all_models(self):
        query = f'SELECT * FROM {self.table}'
        self.cursor.execute(query)
        models = self.cursor.fetchall()

        if not models:
            print(f'Table {self.table} is empty!')
        else:
            for model_data in models:
                model = Model(
                    url=model_data[1], model_code=model_data[2], barcode=model_data[3], name_en=model_data[4], name_tr=model_data[5], description_en=model_data[6], description_tr=model_data[7], template_description_en=model_data[8], template_description_tr=model_data[9], total_price=model_data[10], volume=model_data[11], status=model_data[12], stl_size=model_data[13]
                )
                print(model)


    def update_model(self, model_code: str, model: Model):
        query = f'''
        UPDATE {self.table}
        SET Link = ?, Barcode = ?, NameEN = ?, NameTR = ?, DescriptionEN = ?, DescriptionTR = ?, TemplateDescriptionEN = ?, TemplateDescriptionTR = ?, TotalPrice = ?, Volume = ?, Status = ?, Size1 = ?
        WHERE Code = ?
        '''
        self.cursor.execute(query, (
            model.url, model.barcode, model.name_en, model.name_tr, model.description_en,
            model.description_tr, model.template_description_en, model.template_description_tr, model.total_price, model.volume, model.status, model.stl_size,
            model_code
        ))
        self.connection.commit()


    def update_column(self, model_code: str, column: str, new_value):
        valid_columns = {'Link', 'Code', 'Barcode', 'NameEN', 'NameTR', 'DescriptionEN', 'DescriptionTR', 'TemplateDescriptionEN', 'TemplateDescriptionTR', 'TotalPrice', 'Volume', 'Status', 'Size1'}
        if column not in valid_columns:
            print(f'Invalid column: {column}. Valid columns are: {valid_columns}')
            return

        query = f'SELECT * FROM {self.table} WHERE Code = ?'
        self.cursor.execute(query, (model_code,))
        models = self.cursor.fetchall()
        if not models:
            print(f'Model with Code {model_code} not found!')
        else:
            update_query = f'UPDATE {self.table} SET {column} = ? WHERE Code = ?'
            self.cursor.execute(update_query, (new_value, model_code))
            self.connection.commit()
            print(f'Model with Code {model_code} updated successfully!')


    def search_and_export(self, keyword: str, export_path: str = None):
        query = f'''
        SELECT * FROM {self.table}
        WHERE Code LIKE ? OR Barcode LIKE ? OR NameEN LIKE ? OR NameTR LIKE ? OR DescriptionEN LIKE ? OR DescriptionTR LIKE ? OR TemplateDescriptionEN LIKE ? OR TemplateDescriptionTR LIKE ? OR Status LIKE ?
        '''
        keyword = f"%{keyword}%"
        self.cursor.execute(query, (keyword, keyword, keyword, keyword, keyword, keyword, keyword, keyword, keyword))
        results = self.cursor.fetchall()

        if not results:
            print("No matching records found.")
            return

        columns = ['ID', 'Link', 'Code', 'Barcode', 'NameEN', 'NameTR', 'DescriptionEN', 'DescriptionTR', 'TemplateDescriptionEN', 'TemplateDescriptionTR', 'TotalPrice', 'Volume', 'Status', 'Size1']
        df = pd.DataFrame(results, columns=columns)

        print("Matching records:")
        print(df)

        if export_path:
            df.to_excel(export_path, index=False)
            print(f"Results exported to {export_path}")


    def update_xml_with_excel(self):
        if not os.path.exists('thangs.xml'):
            print(f"Hata: thangs.xml dosyası bulunamadı!")
            return
        
        os.remove('thangs.xml')
        df = pd.read_excel('thangs.xlsx')
        df[df['Status'] == 'aktif'].to_xml('thangs.xml', index=False)
        print('Aktif olan ürünler thangs.xml adlı dosyaya kaydedildi.')



class ExcelToDBTool:
    def __init__(self, db: str, table_name: str):
        self.model_db = ModelDB(db=db, table=table_name)


    def process_excel(self, excel_path: str):
        df = pd.read_excel(excel_path)
        required_columns = ['Link', 'Code', 'Barcode', 'NameEN', 'NameTR', 'DescriptionEN', 'DescriptionTR', 'TemplateDescriptionEN', 'TemplateDescriptionTR', 'TotalPrice', 'Volume', 'Status', 'Size1']
        
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f'Excel file must contain the following columns: {required_columns}')

        for _, row in df.iterrows():
            model = Model(
                url=row['Link'],
                model_code=row['Code'],
                barcode=row['Barcode'],
                name_en=row['NameEN'],
                name_tr=row['NameTR'],
                description_en=row['DescriptionEN'],
                description_tr=row['DescriptionTR'],
                template_description_en=row['TemplateDescriptionEN'],
                template_description_tr=row['TemplateDescriptionTR'],
                total_price=row['TotalPrice'],
                volume=row['Volume'],
                status=row['Status'],
                stl_size=row['Size1']
            )

            if self.model_db.check_model(model.model_code):
                print(f'Model with Code {model.model_code} already exists. Skipping...')
            else:
                self.model_db.add_model(model)

    def close(self):
        self.model_db.disconnect()


class ExcelToDBUpdateTool:
    def __init__(self, db_path: str, table_name: str):
        self.model_db = ModelDB(db=db_path, table=table_name)


    def process_excel(self, excel_path: str):
        df = pd.read_excel(excel_path)
        required_columns = ['Link', 'Code', 'Barcode', 'NameEN', 'NameTR', 'DescriptionEN', 'DescriptionTR', 'TemplateDescriptionEN', 'TemplateDescriptionTR', 'TotalPrice', 'Volume', 'Status', 'Size1']
        
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f'Excel file must contain the following columns: {required_columns}')

        for _, row in df.iterrows():
            model = Model(
                url=row['Link'],
                model_code=row['Code'],
                barcode=row['Barcode'],
                name_en=row['NameEN'],
                name_tr=row['NameTR'],
                description_en=row['DescriptionEN'],
                description_tr=row['DescriptionTR'],
                template_description_en=row['TemplateDescriptionEN'],
                template_description_tr=row['TemplateDescriptionTR'],
                total_price=row['TotalPrice'],
                volume=row['Volume'],
                status=row['Status'],
                stl_size=row['Size1']
            )

            if self.model_db.check_model(model.model_code):
                print(f'Model with Code {model.model_code} exists. Updating...')
                self.model_db.delete_model(model.model_code)
                self.model_db.add_model(model)
            else:
                print(f'Model with Code {model.model_code} does not exist. Adding...')
                self.model_db.add_model(model)


    def close(self):
        self.model_db.disconnect()