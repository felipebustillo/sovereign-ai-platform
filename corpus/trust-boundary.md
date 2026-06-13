# Trust boundary

The platform is built around a single security principle: agent reasoning is
separated from agent action. The inference host generates and transforms
information, but it is never given the credentials required to change other
systems.

## What the inference host must not hold

The host that runs inference must not be given SSH keys to other machines,
source-control tokens with write scope, or cloud API keys beyond the inference
scope. The one allowed exception is pulling model weights from Hugging Face.

## Why the boundary exists

Any prompt or tool call that runs on the inference host should be confined to
information operations: reading, generating, and transforming text. It should not
be able to perform infrastructure operations such as deploying, rotating secrets,
or deleting resources. Because the host holds no privileged credentials, a prompt
injection or a misbehaving agent cannot turn a text operation into an
infrastructure change.

## Where privileged work goes

If a workflow genuinely needs privileged automation, that workflow runs on a
separate host on a different security boundary. It is not added to the n8n
instance on the inference host.

## Network exposure

All HTTP ports bind to the host's internal interface. The stack is never exposed
to the public internet directly. When public access is required, it goes through
a separate reverse-proxy host that terminates TLS, never straight from the
inference host.
