
class Categories:
    def __init__(self):
        self.categories = [
            {
                'id': 1,
                'name': 'Trending',
                'url': 'https://thangs.com/?sort=trending&range=trending#content'
            },

            {
                'id': 2,
                'name': 'Popular', 
                'url': 'https://thangs.com/?sort=likes&range=week#content'
            },

            {
                'id': 3,
                'name': 'New Uploads',
                'url': 'https://thangs.com/?sort=date#content'
            },

            {
                'id': 4,
                'name': 'Downloads',
                'url': 'https://thangs.com/?sort=downloaded&range=week#content'
            },
            
            {
                'id': 5,
                'name': '3D Printers',
                'url': 'https://thangs.com/category/3D%20Printers?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 6,
                'name': 'Articulated',
                'url': 'https://thangs.com/category/Articulated?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 7,
                'name': 'Art',
                'url': 'https://thangs.com/category/Art?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 8,
                'name': 'Costumes & Cosplay',
                'url': 'https://thangs.com/category/Costumes%20%26%20Cosplay?sort=likes&explore=true&range=year'
            },
            
            {
                'id': 9,
                'name': 'Education',
                'url': 'https://thangs.com/category/Education?sort=likes&explore=true&range=year'
            },
            
            {
                'id': 10,
                'name': 'Fashion',
                'url': 'https://thangs.com/category/Fashion?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 11,
                'name': 'Functional',
                'url': 'https://thangs.com/category/Functional?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 12,
                'name': 'Gridfinity',
                'url': 'https://thangs.com/category/Gridfinity?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 13,
                'name': 'Health & Fitness',
                'url': 'https://thangs.com/category/Health%20%26%20Fitness?sort=likes&explore=true&range=year'
            },
            
            {
                'id': 14,
                'name': 'Hobbies',
                'url': 'https://thangs.com/category/Hobbies?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 15,
                'name': 'Home',
                'url': 'https://thangs.com/category/Home?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 16,
                'name': 'Multiboard',
                'url': 'https://thangs.com/category/Multiboard?sort=likes&explore=true&range=year'
            },
            
            {
                'id': 17,
                'name': 'Pop Culture',
                'url': 'https://thangs.com/category/Pop%20Culture?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 18,
                'name': 'Print In Place',
                'url': 'https://thangs.com/category/Print%20In%20Place?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 19,
                'name': 'Seasonal',
                'url': 'https://thangs.com/category/Seasonal?sort=likes&explore=true&range=month'
            },
            
            {
                'id': 20,
                'name': 'Toys & Games',
                'url': 'https://thangs.com/category/Toys%20%26%20Games?sort=likes&explore=true&range=month'
            },

            {
                'id': 21,
                'name': 'Keyword Ara',
                'url': 'https://thangs.com/search/<KEYWORD>?scope=thangs&view=grid&freeModels=true&domains=Thangs'
            }
        ]


    def list_categories(self):
        for category in self.categories:
            print(f'{category["id"]}. {category["name"]}')
        return self.categories
    

if __name__ == '__main__':
    cat = Categories()
    cat.list_categories()