# Tool manifests

All tools that generate something provide on success a manifest detailing what it did.
Those manifests on storage are formatted as JSON objects.
The object format is heavily inspired by the [Kubernetes](https://kubernetes.io/) API,
so a lot of the [Kubernetes API conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)
can be seen in it.

Currently two types of tools write manifests:
* the [build](build.md) process and
* the [upload](upload.md) tools.

Also see this projects [conventions](conventions.md) and [used labels](labels.md).
