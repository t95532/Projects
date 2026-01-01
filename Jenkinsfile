pipeline {
    agent any

    stages {
        stage('Checkout Source') {
            steps {
                git url: 'https://github.com/t95532/Projects.git', branch: 'main'
            }
        }
        stage('Show Last Commit') {
            steps {
                sh '''
                  echo "Last commit:"
                  git log -1 --pretty=format:"%h by %an — %s"
                '''
            }
        }
    }
}

