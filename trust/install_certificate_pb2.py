# Generated by the protocol buffer compiler.  DO NOT EDIT!

from google.protobuf import descriptor
from google.protobuf import message
from google.protobuf import reflection
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)



DESCRIPTOR = descriptor.FileDescriptor(
  name='install-certificate.proto',
  package='',
  serialized_pb='\n\x19install-certificate.proto\"\xec\x01\n InstallCertificateCommandMessage\x12M\n\x07\x63ommand\x18\xdf\x01 \x02(\x0b\x32;.InstallCertificateCommandMessage.InstallCertificateCommand\x1a\x1a\n\x04Name\x12\x12\n\ncomponents\x18\x08 \x03(\x0c\x1a]\n\x19InstallCertificateCommand\x12@\n\x0f\x63\x65rtificateName\x18\xde\x01 \x02(\x0b\x32&.InstallCertificateCommandMessage.Name')




_INSTALLCERTIFICATECOMMANDMESSAGE_NAME = descriptor.Descriptor(
  name='Name',
  full_name='InstallCertificateCommandMessage.Name',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='components', full_name='InstallCertificateCommandMessage.Name.components', index=0,
      number=8, type=12, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=145,
  serialized_end=171,
)

_INSTALLCERTIFICATECOMMANDMESSAGE_INSTALLCERTIFICATECOMMAND = descriptor.Descriptor(
  name='InstallCertificateCommand',
  full_name='InstallCertificateCommandMessage.InstallCertificateCommand',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='certificateName', full_name='InstallCertificateCommandMessage.InstallCertificateCommand.certificateName', index=0,
      number=222, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=173,
  serialized_end=266,
)

_INSTALLCERTIFICATECOMMANDMESSAGE = descriptor.Descriptor(
  name='InstallCertificateCommandMessage',
  full_name='InstallCertificateCommandMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='command', full_name='InstallCertificateCommandMessage.command', index=0,
      number=223, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_INSTALLCERTIFICATECOMMANDMESSAGE_NAME, _INSTALLCERTIFICATECOMMANDMESSAGE_INSTALLCERTIFICATECOMMAND, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=30,
  serialized_end=266,
)

_INSTALLCERTIFICATECOMMANDMESSAGE_NAME.containing_type = _INSTALLCERTIFICATECOMMANDMESSAGE;
_INSTALLCERTIFICATECOMMANDMESSAGE_INSTALLCERTIFICATECOMMAND.fields_by_name['certificateName'].message_type = _INSTALLCERTIFICATECOMMANDMESSAGE_NAME
_INSTALLCERTIFICATECOMMANDMESSAGE_INSTALLCERTIFICATECOMMAND.containing_type = _INSTALLCERTIFICATECOMMANDMESSAGE;
_INSTALLCERTIFICATECOMMANDMESSAGE.fields_by_name['command'].message_type = _INSTALLCERTIFICATECOMMANDMESSAGE_INSTALLCERTIFICATECOMMAND
DESCRIPTOR.message_types_by_name['InstallCertificateCommandMessage'] = _INSTALLCERTIFICATECOMMANDMESSAGE

class InstallCertificateCommandMessage(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  
  class Name(message.Message):
    __metaclass__ = reflection.GeneratedProtocolMessageType
    DESCRIPTOR = _INSTALLCERTIFICATECOMMANDMESSAGE_NAME
    
    # @@protoc_insertion_point(class_scope:InstallCertificateCommandMessage.Name)
  
  class InstallCertificateCommand(message.Message):
    __metaclass__ = reflection.GeneratedProtocolMessageType
    DESCRIPTOR = _INSTALLCERTIFICATECOMMANDMESSAGE_INSTALLCERTIFICATECOMMAND
    
    # @@protoc_insertion_point(class_scope:InstallCertificateCommandMessage.InstallCertificateCommand)
  DESCRIPTOR = _INSTALLCERTIFICATECOMMANDMESSAGE
  
  # @@protoc_insertion_point(class_scope:InstallCertificateCommandMessage)

# @@protoc_insertion_point(module_scope)
