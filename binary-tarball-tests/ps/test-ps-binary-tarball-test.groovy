pipeline {
    agent {
        label 'docker'
    }
    environment {
        PRODUCT_TO_TEST = "${params.PRODUCT_TO_TEST}"
        PS_VERSION = ''  // Declare PS_VERSION as an environment variable
        PS_REVISION = '' // Declare PS_REVISION as an environment variable
    }
    parameters {
        choice(
            choices: ['ps_80', 'ps_84', 'ps_lts_innovation', 'client_test'],
            description: 'Choose the product version to test',
            name: 'product_to_test'
        )
        booleanParam(
            defaultValue: false, 
            name: 'BUILD_TYPE_MINIMAL'
        )
    }
    stages {
        stage('SET PS_VERSION and PS_REVISION') {
            steps {
                script {
                    // Clone the repo and capture PS_VERSION and PS_REVISION
                    def versionData = sh(script: '''
                        git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                        cd package-testing/VERSIONS
                        PS_VERSION=$(grep ${PRODUCT_TO_TEST} VERSIONS | awk -F= '{print $2}' | sed 's/"//g')
                        PS_REVISION=$(grep ${PRODUCT_TO_TEST} VERSIONS | awk -F= '{print $2}' | sed 's/"//g')
                        echo "PS_VERSION: ${PS_VERSION}"
                        echo "PS_REVISION: ${PS_REVISION}"
                        echo PS_VERSION=${PS_VERSION}
                        echo PS_REVISION=${PS_REVISION}
                    ''', returnStdout: true).trim()

                    // Capture the output and set them as environment variables
                    def versionOutput = versionData.split("\n")
                    env.PS_VERSION = versionOutput.find { it.startsWith('PS_VERSION') }.split('=')[1].trim()
                    env.PS_REVISION = versionOutput.find { it.startsWith('PS_REVISION') }.split('=')[1].trim()

                    // Output to Jenkins console for debugging
                    echo "PS_VERSION: ${env.PS_VERSION}"
                    echo "PS_REVISION: ${env.PS_REVISION}"
                    
                    // Set the build display name
                    currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                }
            }
        }
        stage('Binary tarball test') {
            parallel {
                stage('Ubuntu Noble') {
                    agent {
                        label "min-noble-x64"
                    }
                    steps {
                        script {
                            currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                        }
                        sh '''
                            echo ${BUILD_TYPE_MINIMAL}
                            MINIMAL=""
                            if [ "${BUILD_TYPE_MINIMAL}" = "true" ]; then
                                MINIMAL="-minimal"
                            fi
                            if [ -f /usr/bin/yum ]; then
                                sudo yum install -y git wget
                            else
                                sudo apt install -y git wget
                            fi
                            TARBALL_NAME="Percona-Server-${PS_VERSION}-Linux.x86_64.glibc2.35${MINIMAL}.tar.gz"
                            TARBALL_LINK="https://downloads.percona.com/downloads/TESTING/ps-${PS_VERSION}/"
                            rm -rf package-testing
                            git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                            cd package-testing/binary-tarball-tests/ps
                            wget -q ${TARBALL_LINK}${TARBALL_NAME}
                            ./run.sh || true
                        '''
                        junit 'package-testing/binary-tarball-tests/ps/report.xml'
                    }
                }
                stage('Ubuntu Jammy') {
                    agent {
                        label "min-jammy-x64"
                    }
                    steps {
                        script {
                            currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                        }
                        sh '''
                            echo ${BUILD_TYPE_MINIMAL}
                            MINIMAL=""
                            if [ "${BUILD_TYPE_MINIMAL}" = "true" ]; then
                                MINIMAL="-minimal"
                            fi
                            if [ -f /usr/bin/yum ]; then
                                sudo yum install -y git wget
                            else
                                sudo apt install -y git wget
                            fi
                            TARBALL_NAME="Percona-Server-${PS_VERSION}-Linux.x86_64.glibc2.35${MINIMAL}.tar.gz"
                            TARBALL_LINK="https://downloads.percona.com/downloads/TESTING/ps-${PS_VERSION}/"
                            rm -rf package-testing
                            git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                            cd package-testing/binary-tarball-tests/ps
                            wget -q ${TARBALL_LINK}${TARBALL_NAME}
                            ./run.sh || true
                        '''
                        junit 'package-testing/binary-tarball-tests/ps/report.xml'
                    }
                }
                stage('Ubuntu Focal') {
                    agent {
                        label "min-focal-x64"
                    }
                    steps {
                        script {
                            currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                        }
                        sh '''
                            echo ${BUILD_TYPE_MINIMAL}
                            MINIMAL=""
                            if [ "${BUILD_TYPE_MINIMAL}" = "true" ]; then
                                MINIMAL="-minimal"
                            fi
                            if [ -f /usr/bin/yum ]; then
                                sudo yum install -y git wget
                            else
                                sudo apt install -y git wget
                            fi
                            TARBALL_NAME="Percona-Server-${PS_VERSION}-Linux.x86_64.glibc2.31${MINIMAL}.tar.gz"
                            TARBALL_LINK="https://downloads.percona.com/downloads/TESTING/ps-${PS_VERSION}/"
                            rm -rf package-testing
                            git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                            cd package-testing/binary-tarball-tests/ps
                            wget -q ${TARBALL_LINK}${TARBALL_NAME}
                            ./run.sh || true
                        '''
                        junit 'package-testing/binary-tarball-tests/ps/report.xml'
                    }
                }
                stage('Debian Bookworm') {
                    agent {
                        label "min-bookworm-x64"
                    }
                    steps {
                        script {
                            currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                        }
                        sh '''
                            echo ${BUILD_TYPE_MINIMAL}
                            MINIMAL=""
                            if [ "${BUILD_TYPE_MINIMAL}" = "true" ]; then
                                MINIMAL="-minimal"
                            fi
                            if [ -f /usr/bin/yum ]; then
                                sudo yum install -y git wget
                            else
                                sudo apt install -y git wget
                            fi
                            TARBALL_NAME="Percona-Server-${PS_VERSION}-Linux.x86_64.glibc2.35${MINIMAL}.tar.gz"
                            TARBALL_LINK="https://downloads.percona.com/downloads/TESTING/ps-${PS_VERSION}/"
                            rm -rf package-testing
                            git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                            cd package-testing/binary-tarball-tests/ps
                            wget -q ${TARBALL_LINK}${TARBALL_NAME}
                            ./run.sh || true
                        '''
                        junit 'package-testing/binary-tarball-tests/ps/report.xml'
                    }
                }
                stage('Debian Bullseye') {
                    agent {
                        label "min-bullseye-x64"
                    }
                    steps {
                        script {
                            currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                        }
                        sh '''
                            echo ${BUILD_TYPE_MINIMAL}
                            MINIMAL=""
                            if [ "${BUILD_TYPE_MINIMAL}" = "true" ]; then
                                MINIMAL="-minimal"
                            fi
                            if [ -f /usr/bin/yum ]; then
                                sudo yum install -y git wget
                            else
                                sudo apt install -y git wget
                            fi
                            TARBALL_NAME="Percona-Server-${PS_VERSION}-Linux.x86_64.glibc2.31${MINIMAL}.tar.gz"
                            TARBALL_LINK="https://downloads.percona.com/downloads/TESTING/ps-${PS_VERSION}/"
                            rm -rf package-testing
                            git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                            cd package-testing/binary-tarball-tests/ps
                            wget -q ${TARBALL_LINK}${TARBALL_NAME}
                            ./run.sh || true
                        '''
                        junit 'package-testing/binary-tarball-tests/ps/report.xml'
                    }
                }
                stage('Oracle Linux 9') {
                    agent {
                        label "min-ol-9-x64"
                    }
                    steps {
                        script {
                            currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                        }
                        sh '''
                            echo ${BUILD_TYPE_MINIMAL}
                            MINIMAL=""
                            if [ "${BUILD_TYPE_MINIMAL}" = "true" ]; then
                                MINIMAL="-minimal"
                            fi
                            if [ -f /usr/bin/yum ]; then
                                sudo yum install -y git wget
                            else
                                sudo apt install -y git wget
                            fi
                            TARBALL_NAME="Percona-Server-${PS_VERSION}-Linux.x86_64.glibc2.34${MINIMAL}.tar.gz"
                            TARBALL_LINK="https://downloads.percona.com/downloads/TESTING/ps-${PS_VERSION}/"
                            rm -rf package-testing
                            git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                            cd package-testing/binary-tarball-tests/ps
                            wget -q ${TARBALL_LINK}${TARBALL_NAME}
                            ./run.sh || true
                        '''
                        junit 'package-testing/binary-tarball-tests/ps/report.xml'
                    }
                }
                stage('Oracle Linux 8') {
                    agent {
                        label "min-ol-8-x64"
                    }
                    steps {
                        script {
                            currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                        }
                        sh '''
                            echo ${BUILD_TYPE_MINIMAL}
                            MINIMAL=""
                            if [ "${BUILD_TYPE_MINIMAL}" = "true" ]; then
                                MINIMAL="-minimal"
                            fi
                            if [ -f /usr/bin/yum ]; then
                                sudo yum install -y git wget
                            else
                                sudo apt install -y git wget
                            fi
                            TARBALL_NAME="Percona-Server-${PS_VERSION}-Linux.x86_64.glibc2.28${MINIMAL}.tar.gz"
                            TARBALL_LINK="https://downloads.percona.com/downloads/TESTING/ps-${PS_VERSION}/"
                            rm -rf package-testing
                            git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                            cd package-testing/binary-tarball-tests/ps
                            wget -q ${TARBALL_LINK}${TARBALL_NAME}
                            ./run.sh || true
                        '''
                        junit 'package-testing/binary-tarball-tests/ps/report.xml'
                    }
                }
                stage('Centos 7') {
                    agent {
                        label "min-centos-7-x64"
                    }
                    steps {
                        script {
                            currentBuild.displayName = "#${BUILD_NUMBER}-${env.PS_VERSION}-${env.PS_REVISION}"
                        }
                        sh '''
                            echo ${BUILD_TYPE_MINIMAL}
                            MINIMAL=""
                            if [ "${BUILD_TYPE_MINIMAL}" = "true" ]; then
                                MINIMAL="-minimal"
                            fi
                            if [ -f /usr/bin/yum ]; then
                                sudo yum install -y git wget
                            else
                                sudo apt install -y git wget
                            fi
                            TARBALL_NAME="Percona-Server-${PS_VERSION}-Linux.x86_64.glibc2.17${MINIMAL}.tar.gz"
                            TARBALL_LINK="https://downloads.percona.com/downloads/TESTING/ps-${PS_VERSION}/"
                            rm -rf package-testing
                            git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                            cd package-testing/binary-tarball-tests/ps
                            wget -q ${TARBALL_LINK}${TARBALL_NAME}
                            ./run.sh || true
                        '''
                        junit 'package-testing/binary-tarball-tests/ps/report.xml'
                    }
                }
            }
        }
    }
}
