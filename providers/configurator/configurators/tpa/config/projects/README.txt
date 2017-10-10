index.json
==========
This file lists summary of all projects.

{
    "file": {
        "title": "Index file for all projects",             /* Title of this file for display purpose. */
        "format": "json",                                   /* Format of this file. */
        "category_id": projects_index"                      /* Configuration file category. */
    },

    "projects": [
        {
            "id": "sample",                                             /* Project ID. Has to be unique. */ 
                                                                        /* This ID is also used for the project's directory name. */
                                                                        /*   e.g. config/projects/sample */

            "config_path": "config/projects/sample/project.json",       /* Project configuration file location of the project. */
                                                                        /* This is a relative path to configurator script. */

            "desc": "Sample project."                                   /* Brief description of the project. */
        },
        
        ....

    ]
}


