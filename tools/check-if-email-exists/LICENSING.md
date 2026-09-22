# Licensing: what AGPL-3.0 means for how we use this

check-if-email-exists is AGPL-3.0. That license has a network clause most open
source licenses do not, and it decides where this tool can live.

## Safe: internal use

Running the CLI or the backend on our own infrastructure, for our own list
hygiene, with no outside party interacting with it over a network, triggers no
distribution and no source obligation. That is what everything in this directory
is built for. Nothing to do.

## Not safe: anything customer-facing

AGPL section 13 says that if users interact with a modified version of the
program remotely through a computer network, they must be offered the
corresponding source. Two consequences worth being precise about:

1. If verification is exposed as a feature inside Amplifier Find, or any product
   surface a customer touches, that is remote network interaction. The obligation
   attaches to the modified program and whatever the FSF and a court would treat
   as the same work, which for a linked Rust binary is a broad reading.
2. The risk is not theoretical dilution of the dataset or the model. Sona-2 and
   the corpus are separate works and are not reached by running a separate
   verification binary. The exposure is the service code around it.

## The decision, if it ever comes up

Reacher sells a commercial license precisely for the customer-facing case. If
verification ever becomes a product feature rather than an internal sales
operation, buy it before shipping, not after. It is cheap relative to the cost of
having the question asked during diligence.

Keep the line clean: this directory is internal tooling. If someone proposes
wiring it into a product path, that is a licensing decision, not an engineering
one.
