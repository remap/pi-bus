# Generated by the protocol buffer compiler.  DO NOT EDIT!

from google.protobuf import descriptor
from google.protobuf import message
from google.protobuf import reflection
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)



DESCRIPTOR = descriptor.FileDescriptor(
  name='new-environment.proto',
  package='',
  serialized_pb='\n\x15new-environment.proto\"\xd8\x01\n\x1cNewEnvironmentCommandMessage\x12\x45\n\x07\x63ommand\x18\xdd\x01 \x02(\x0b\x32\x33.NewEnvironmentCommandMessage.NewEnvironmentCommand\x1a\x1a\n\x04Name\x12\x12\n\ncomponents\x18\x08 \x03(\x0c\x1aU\n\x15NewEnvironmentCommand\x12<\n\x0f\x65nvironmentName\x18\xdc\x01 \x02(\x0b\x32\".NewEnvironmentCommandMessage.Name')




_NEWENVIRONMENTCOMMANDMESSAGE_NAME = descriptor.Descriptor(
  name='Name',
  full_name='NewEnvironmentCommandMessage.Name',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='components', full_name='NewEnvironmentCommandMessage.Name.components', index=0,
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
  serialized_start=129,
  serialized_end=155,
)

_NEWENVIRONMENTCOMMANDMESSAGE_NEWENVIRONMENTCOMMAND = descriptor.Descriptor(
  name='NewEnvironmentCommand',
  full_name='NewEnvironmentCommandMessage.NewEnvironmentCommand',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='environmentName', full_name='NewEnvironmentCommandMessage.NewEnvironmentCommand.environmentName', index=0,
      number=220, type=11, cpp_type=10, label=2,
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
  serialized_start=157,
  serialized_end=242,
)

_NEWENVIRONMENTCOMMANDMESSAGE = descriptor.Descriptor(
  name='NewEnvironmentCommandMessage',
  full_name='NewEnvironmentCommandMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='command', full_name='NewEnvironmentCommandMessage.command', index=0,
      number=221, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_NEWENVIRONMENTCOMMANDMESSAGE_NAME, _NEWENVIRONMENTCOMMANDMESSAGE_NEWENVIRONMENTCOMMAND, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=26,
  serialized_end=242,
)

_NEWENVIRONMENTCOMMANDMESSAGE_NAME.containing_type = _NEWENVIRONMENTCOMMANDMESSAGE;
_NEWENVIRONMENTCOMMANDMESSAGE_NEWENVIRONMENTCOMMAND.fields_by_name['environmentName'].message_type = _NEWENVIRONMENTCOMMANDMESSAGE_NAME
_NEWENVIRONMENTCOMMANDMESSAGE_NEWENVIRONMENTCOMMAND.containing_type = _NEWENVIRONMENTCOMMANDMESSAGE;
_NEWENVIRONMENTCOMMANDMESSAGE.fields_by_name['command'].message_type = _NEWENVIRONMENTCOMMANDMESSAGE_NEWENVIRONMENTCOMMAND
DESCRIPTOR.message_types_by_name['NewEnvironmentCommandMessage'] = _NEWENVIRONMENTCOMMANDMESSAGE

class NewEnvironmentCommandMessage(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  
  class Name(message.Message):
    __metaclass__ = reflection.GeneratedProtocolMessageType
    DESCRIPTOR = _NEWENVIRONMENTCOMMANDMESSAGE_NAME
    
    # @@protoc_insertion_point(class_scope:NewEnvironmentCommandMessage.Name)
  
  class NewEnvironmentCommand(message.Message):
    __metaclass__ = reflection.GeneratedProtocolMessageType
    DESCRIPTOR = _NEWENVIRONMENTCOMMANDMESSAGE_NEWENVIRONMENTCOMMAND
    
    # @@protoc_insertion_point(class_scope:NewEnvironmentCommandMessage.NewEnvironmentCommand)
  DESCRIPTOR = _NEWENVIRONMENTCOMMANDMESSAGE
  
  # @@protoc_insertion_point(class_scope:NewEnvironmentCommandMessage)

# @@protoc_insertion_point(module_scope)
