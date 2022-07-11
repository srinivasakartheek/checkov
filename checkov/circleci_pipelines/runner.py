from __future__ import annotations
import jmespath
import os
from typing import TYPE_CHECKING
from checkov.common.images.image_referencer import ImageReferencer, Image
from checkov.common.output.report import CheckType
from checkov.circleci_pipelines.registry import registry
from checkov.yaml_doc.runner import Runner as YamlRunner

WORKFLOW_DIRECTORY = "circleci"

class Runner(YamlRunner, ImageReferencer):
    check_type = CheckType.CIRCLECI_PIPELINES  # noqa: CCE003  # a static attribute

    def __init__(self):
        super().__init__()

    def require_external_checks(self):
        return False

    def import_registry(self):
        return registry

    def included_paths(self):
        return [".circleci"]

    def _parse_file(self, f):
        if self.is_workflow_file(f):
            return super()._parse_file(f)

    def is_workflow_file(self, file_path):
        """
        :return: True if the file mentioned is named config.yml/yaml in .circleci dir from included_paths(). Otherwise: False
        """
        abspath = os.path.abspath(file_path)
        return WORKFLOW_DIRECTORY in abspath and abspath.endswith(("config.yml", "config.yaml"))

    def get_images(self, file_path):
        """
        Get container images mentioned in a file
        :param file_path: File to be inspected

        File sample that will return 5 Image objects:
            # # Use the latest 2.1 version of CircleCI pipeline process engine.
            # # See: https://circleci.com/docs/2.0/configuration-reference
            # version: 2.1
            # # Define a job to be invoked later in a workflow.
            # # See: https://circleci.com/docs/2.0/configuration-reference/#jobs
            # jobs:
            # say-hello:
            #    docker:
            #    - image: buildpack-deps:latest # primary container
            #        auth:
            #        username: mydockerhub-user
            #        password: $DOCKERHUB_PASSWORD  # context / project UI env-var reference
            #        environment:
            #        ENV: CI
            #    - image: mongo:2.6.8
            #        auth:
            #        username: mydockerhub-user
            #        password: $DOCKERHUB_PASSWORD  # context / project UI env-var reference
            #        command: [--smallfiles]
            #    - image: postgres:14.2
            #        auth:
            #        username: mydockerhub-user
            #        password: $DOCKERHUB_PASSWORD  # context / project UI env-var reference
            #        environment:
            #        POSTGRES_USER: user
            #    - image: redis@sha256:54057dd7e125ca41afe526a877e8bd35ec2cdd33b9217e022ed37bdcf7d09673
            #        auth:
            #        username: mydockerhub-user
            #        password: $DOCKERHUB_PASSWORD  # context / project UI env-var reference
            #    - image: acme-private/private-image:321
            #        auth:
            #        username: mydockerhub-user
            #        password: $DOCKERHUB_PASSWORD  # context / project UI env-var reference
            # # Invoke jobs via workflows
            # # See: https://circleci.com/docs/2.0/configuration-reference/#workflows
            # workflows:
            # say-hello-workflow:
            #     jobs:
            #     - say-hello
        :return: List of container image objects mentioned in the file.

        """

        images = set()

        workflow, workflow_line_numbers = self._parse_file(file_path)
        self.add_docker_job_images(workflow, images, file_path)

        return images

    def add_docker_job_images(self, workflow: dict, images: set, file_path: str) -> None:
        """

        :param workflow: parsed workflow file
        :param images: set of images to be updated
        :param file_path: path of analyzed workflow
        """

        # Only 'docker' executor paths are supported. (machine, windows & osx executors do not yeild OCI compatible images see https://circleci.com/docs/2.0/configuration-reference#docker-machine-macos-windows-executor)
        keywords = [
            'jobs.*.docker[].{image: image, __startline__: __startline__, __endline__:__endline__}']
        for keyword in keywords:
            results = jmespath.search(keyword, workflow)
            for result in results:
                image_name = result.get("image", None)
                if image_name:
                    image_id = self.inspect(image_name)
                    image_obj = Image(file_path=file_path, name=image_name, image_id=image_id,
                                      start_line=result["__startline__"],
                                      end_line=result["__endline__"])
                    images.add(image_obj)

    # def add_root_image(self, file_path: str, images: set,
    #                    workflow_line_numbers: dict, workflow: dict) -> None:
    #     root_image = workflow.get("image", "")

    #     if root_image:
    #         for line_number, line_txt in workflow_line_numbers:
    #             if "image" in line_txt and not line_txt.startswith(' '):
    #                 image_id = self.inspect(root_image)
    #                 image_obj = Image(
    #                     file_path=file_path,
    #                     name=root_image,
    #                     image_id=image_id,
    #                     start_line=line_number,
    #                     end_line=line_number,
    #                 )
    #                 images.add(image_obj)
