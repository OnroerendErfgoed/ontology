Relations
=========

Dealing with relations between information objects. Options:

 * Define all ourselves so we can restrict domains and ranges maximally.
 * Maximum re-use, eg. from Dublin Core.

Dublin Core
-----------

Defines the following relations:

 * http://purl.org/dc/terms/relation: Abstract relation
 * http://purl.org/dc/terms/conformsTo: Conforms to a standard (has range:
   Standard).
 * http://purl.org/dc/terms/hasFormat: Has a certain format.
 * http://purl.org/dc/terms/hasPart: Has a part.
 * http://purl.org/dc/terms/hasVersion: Has a version.
 * http://purl.org/dc/terms/references: A related resource that is referenced,
   cited, or otherwise pointed to by the described resource.
 * http://purl.org/dc/terms/replaces: A related resource that is supplanted,
   displaced, or superseded by the described resource.
 * http://purl.org/dc/terms/requires: A related resource that is required by the
   described resource to support its function, delivery, or coherence.
 * http://purl.org/dc/terms/source: A related resource from which the described
   resource is derived. 
 * http://purl.org/dc/terms/isFormatOf: Inverse of hasFormat.
 * http://purl.org/dc/terms/isPartOf: Inverse of hasPart.
 * http://purl.org/dc/terms/isReferencedBy: Inverse of references.
 * http://purl.org/dc/terms/isReplacedBy: Inverse of replaces.
 * http://purl.org/dc/terms/isRequiredBy: Inverse of requires.
 * http://purl.org/dc/terms/isVersionOf: Inverse of hasVersion.

Issues with Dublin Core:

 * Almost no domains or ranges defined. Only conformsTo seems to have a range.
   Probably more of a good than a bad thing.
 * No inverseOf definitions. It's quite clear that isPartOf is the reverse of
   hasPart, but this has not been defined explicitly. We could just treat it as
   being the inverse or add that explicit definition ourselves like the GRI does
   with it's vocabs.
 
