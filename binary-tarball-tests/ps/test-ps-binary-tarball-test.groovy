pipeline {
    agent {
        label 'docker'
    }
    parameters {
        PRODUCT_TO_TEST = "${params.PRODUCT_TO_TEST}"
        booleanParam(
            defaultValue: false,
            name:'BUILD_TYPE_MINIMAL'
            )
    }
    parameters {
        choice(
            choices: ['ps_80', 'ps_84', 'ps_lts_innovation', 'client_test'],
            description: 'Choose the product version to test',
            name: 'product_to_test'
        )
        string(
            defaultValue: 'https://github.com/Grishma123-Eng/package-testing.git',
            description: 'Repo name',
            name: 'git_repo',
            trim: false
        )
    }
    options {
        withCredentials(moleculePdpsJenkinsCreds())
    }
    stages {
        stage("SET PS_VERSION and PS_REVISION") {
            steps {
                script {
                    // Set the display name of the build
                    currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
                }
                // Shell script to clone the repo and get the PS_VERSION and PS_REVISION
                sh '''
                    # Clone the repository
                    git clone https://github.com/Percona-QA/package-testing.git --branch master --depth 1
                    cd package-testing/VERSIONS

                    # Get PS_VERSION from the VERSIONS file
                    PS_VERSION=$(grep ${PRODUCT_TO_TEST} VERSIONS | awk -F= '{print $2}' | sed 's/"//g')
                    echo "${PS_VERSION}"

                    # Get PS_REVISION from the VERSIONS file
                    PS_REVISION=$(grep ${PRODUCT_TO_TEST} VERSIONS | awk -F= '{print $2}' | sed 's/"//g')
                    echo "${PS_REVISION}"
                '''
                // Capture PS_VERSION and PS_REVISION into Groovy variables
                script {
                    // Extract PS_VERSION and PS_REVISION values after running the shell script
                    PS_VERSION = sh(script: "echo ${PS_VERSION}", returnStdout: true).trim()
                    PS_REVISION = sh(script: "echo ${PS_REVISION}", returnStdout: true).trim()

                    // Output to Jenkins console
                    echo "PS_VERSION: ${PS_VERSION}"
                    echo "PS_REVISION: ${PS_REVISION}"
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
                            currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
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
                            currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
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
                            currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
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
                            currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
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
                            currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
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
                            currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
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
                            currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
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
                            currentBuild.displayName = "#${BUILD_NUMBER}-${PS_VERSION}-${PS_REVISION}"
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
