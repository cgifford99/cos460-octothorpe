import os


class FileUtils(object):
    USER_STORE_FILENAME = 'users.json'
    MAP_FILENAME = 'map.txt'

    @staticmethod
    def get_data_dir(root_path: str) -> str:
        root_path = os.path.abspath(root_path)

        return os.path.join(
            root_path, 'data'
        )

    @staticmethod
    def get_userstore_filepath(root_path: str) -> str:
        root_path = os.path.abspath(root_path)

        return os.path.join(
            FileUtils.get_data_dir(root_path), FileUtils.USER_STORE_FILENAME
        )

    @staticmethod
    def get_map_filepath(root_path: str) -> str:
        root_path = os.path.abspath(root_path)

        return os.path.join(
            FileUtils.get_data_dir(root_path), FileUtils.MAP_FILENAME
        )