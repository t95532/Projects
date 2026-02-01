pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/t95532/Projects.git', branch: 'main'
            }
        }

        stage('Show Last Commit') {
            steps {
                bat '''
                  echo Latest Commit:
                  git log -1 --pretty=format:"%%h | %%an | %%ad | %%s"
                '''
            }
        }
    }
}
