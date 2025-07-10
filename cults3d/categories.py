
class Categories:
    def __init__(self):
        self.categories = [
            {
                'id': 1,
                'name': 'Art',
                'url': 'https://cults3d.com/en/categories/art?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 2,
                'name': 'Fashion',
                'url': 'https://cults3d.com/en/categories/fashion?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 3,
                'name': 'Jewelry',
                'url': 'https://cults3d.com/en/categories/jewelry?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 4,
                'name': 'Home',
                'url': 'https://cults3d.com/en/categories/home?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 5,
                'name': 'Architecture',
                'url': 'https://cults3d.com/en/categories/architecture?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 6,
                'name': 'Gadget',
                'url': 'https://cults3d.com/en/categories/gadget?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 7,
                'name': 'Game',
                'url': 'https://cults3d.com/en/categories/game?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 8,
                'name': 'Tools',
                'url': 'https://cults3d.com/en/categories/tool?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 9,
                'name': 'Naughties',
                'url': 'https://cults3d.com/en/categories/naughties?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

            {
                'id': 10,
                'name': 'Various',
                'url': 'https://cults3d.com/en/categories/various?only_free=true&only_featured=true&page=1&sort=likes_counter'
            },

        ]

    
    def list_categories(self):
        for category in self.categories:
            print(f'{category["id"]}. {category["name"]}')
        return self.categories
    

if __name__ == '__main__':
    cat = Categories()
    cat.list_categories()