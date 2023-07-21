#!/usr/bin/python

'''@restructure_data

This file restructures the supplied data. But, the dataset is left
untouched, and formatted within 'convert_upload.py'.

'''


class Restructure_Data(object):
    '''@Restructure_Data

    This class provides an interface to restructure the supplied data into a
    consistent structure, which allows successive parsers to implement
    corresponding logic.

    Note: this class explicitly inherits the 'new-style' class.

    '''

    def __init__(self, settings, dataset=None):
        '''@__init__

        This constructor is responsible for defining class variables.

        '''

        self.settings = settings
        self.dataset = dataset
        self.list_error = []

        self.type_web = "<class 'werkzeug.datastructures.ImmutableMultiDict'>"
        self.type_programmatic = "<type 'dict'>"

    def restructure(self):
        '''@restructure

        This method restructures the supplied data, into a consistent
        dictionary format. The nested supplied dataset, is left untouched.

        '''

        # local variables
        formatted_settings = {}
        formatted_files = []

        # restructure settings
        try:
            for key, value in self.settings.items():
                # web-interface: 'isinstance' did not work
                if str(type(self.settings)) == self.type_web:
                    for lvalue in self.settings.getlist(key):
                        # base case
                        if key.lower() not in formatted_settings:
                            formatted_settings[key.lower()] = lvalue.lower()
                        else:
                            # step case 1
                            if type(formatted_settings[key.lower()]) == \
                                    unicode:
                                formatted_settings[key.lower()] = [
                                    formatted_settings[key.lower()]
                                ]
                                formatted_settings[key.lower()].append(lvalue)
                            # step case n
                            elif type(formatted_settings[key.lower()]) == list:
                                formatted_settings[key.lower()].append(lvalue)

                # programmatic-interface: 'isinstance' did not work
                elif str(type(self.settings)) == self.type_programmatic:
                    formatted_settings = self.settings

        except Exception as error:
            self.list_error.append(error)
            return {'data': None, 'error': self.list_error}

        # restructure dataset: not all sessions involve files
        if self.dataset:
            try:
                # web-interface: 'isinstance' did not work
                if str(type(self.settings)) == self.type_web:
                    for file in self.dataset.getlist('svm_dataset[]'):
                        formatted_files.append({
                            'filename': file.filename,
                            'file': file
                        })

                    dataset = {
                        'upload_quantity':
                            len(self.dataset.getlist('svm_dataset[]')),
                        'file_upload': formatted_files, 'json_string': None
                    }

                # programmatic-interface: 'isinstance' did not work
                elif str(type(self.settings)) == self.type_programmatic:
                    dataset = {
                        'upload_quantity': 1,
                        'file_upload': None,
                        'json_string': self.dataset
                    }

            except Exception as error:
                self.list_error.append(error)
                return {'data': None, 'error': self.list_error}

        else:
            dataset = None

        # build input structure
        data = {'settings': formatted_settings, 'dataset': dataset}

        # return new structured data
        return {'data': data, 'error': None}

    def get_errors(self):
        '''@get_errors

        This method returns all errors pertaining to the instantiated class.

        '''

        if len(self.list_error) > 0:
            return {'error': self.list_error}
        else:
            return {'error': None}
