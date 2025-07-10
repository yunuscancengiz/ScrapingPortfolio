from models_db import Model, ModelDB, ExcelToDBTool, ExcelToDBUpdateTool


class DBOperations:
    def __init__(self, db_name:str, table:str):
        self.db_name = db_name
        self.table = table
        self.model_db = ModelDB(db=self.db_name, table=self.table)


    def main(self):
        while True:
            print(
            '''
            \n\tDatabase işlemleri:
            -------------------------

            1) Modelleri göster
            2) Model ekle
            3) Model sil
            4) Model kodu ara
            5) Model güncelle
            6) Model sütunu güncelle
            7) Anahtar kelime ara
            8) Toplu ürün ekle (Excel ile)
            9) Toplu ürün güncelle (Excel ile)
            10) Excel ile XML güncelle (aktif ürünler)

            Çıkmak için q tuşuna basın

            -------------------------\n
            '''
            )
            operation = input('\tBir işlem seçin:\n\t> ')

            if operation.lower() == 'q':
                print('Programdan çıkış yapılıyor.')
                self.model_db.disconnect()
                break

            elif operation == '1':
                self.model_db.show_all_models()

            elif operation == '2':
                model = Model(
                    url=input('Link: '),
                    model_code=input('Model kodu: '),
                    barcode=input('Barkod: '),
                    name_en=input('Model Adı(EN): '),
                    name_tr=input('Model Adı(TR): '),
                    description_en=input('Açıklama(EN): '),
                    description_tr=input('Açıklama(TR): '),
                    price=input('Fiyat: '),
                    volume=input('Hacim: '),
                    status=input('Durum: '),
                    stl_size=input('STL Boyutu: ')
                )
                self.model_db.add_model(model=model)

            elif operation == '3':
                model_code = input('Model kodu: ')
                self.model_db.delete_model(model_code=model_code)

            elif operation == '4':
                model_code = input('Model kodu: ')
                response = self.model_db.check_model(model_code=model_code)
                print(response)

            elif operation == '5':
                model_code = input('Model kodu: ')
                model = Model(
                    url=input('Link: '),
                    model_code=input('Model kodu: '),
                    barcode=input('Barkod: '),
                    name_en=input('Model Adı(EN): '),
                    name_tr=input('Model Adı(TR): '),
                    description_en=input('Açıklama(EN): '),
                    description_tr=input('Açıklama(TR): '),
                    price=input('Fiyat: '),
                    volume=input('Hacim: '),
                    status=input('Durum: '),
                    stl_size=input('STL Boyutu: ')
                )
                self.model_db.update_model(model_code=model_code, model=model)

            elif operation == '6':
                model_code = input('Model kodu: ')
                column = input('Sütun: ')
                new_value = input('Güncel değer: ')
                self.model_db.update_column(model_code=model_code, column=column, new_value=new_value)

            elif operation == '7':
                keyword = input('Anahtar kelime: ')
                self.model_db.search_and_export(keyword=keyword)

            elif operation == '8':
                excel_file = input('Excel dosya adı(örnek.xlsx): ')
                excel_to_db = ExcelToDBTool(db=self.db_name, table_name=self.table)
                excel_to_db.process_excel(excel_path=excel_file)
                excel_to_db.close()

            elif operation == '9':
                excel_file = input('Excel dosya adı(örnek.xlsx): ')
                excel_to_db_update = ExcelToDBUpdateTool(db_path=self.db_name, table_name=self.table)
                excel_to_db_update.process_excel(excel_path=excel_file)
                excel_to_db_update.close()
                self.model_db.update_xml_with_excel()

            elif operation == '10':
                self.model_db.update_xml_with_excel()


if __name__ == '__main__':
    db_operations = DBOperations(db_name='Models.db', table='Thangs')
    db_operations.main()